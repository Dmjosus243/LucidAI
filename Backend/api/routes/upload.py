import math
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import pandas as pd
import io
import uuid

from database import get_db
from storage import temp_storage
from api.dependencies import get_current_user
from api.audit import log_action
from database import Profile

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    allowed = [".csv", ".xlsx", ".xls"]
    if not any(file.filename.endswith(ext) for ext in allowed):
        raise HTTPException(400, "Format non supporté. Utilisez CSV ou Excel.")
    
    try:
        contents = await file.read()
        file_id = str(uuid.uuid4())
        
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        df.columns = df.columns.str.strip().str.lower()
        
        temp_storage[file_id] = {
            "df": df,
            "filename": file.filename,
            "user_id": str(user.id),
        }

        log_action(
            db, str(user.id), "file.upload",
            {"filename": file.filename, "rows": len(df)},
            request.client.host if request and request.client else None,
        )
        
        preview = df.head(5).copy()
        for col in preview.columns:
            if pd.api.types.is_datetime64_any_dtype(preview[col]):
                preview[col] = preview[col].dt.strftime("%Y-%m-%d %H:%M:%S")
        records = preview.to_dict(orient="records")
        for row in records:
            for k, v in row.items():
                if isinstance(v, float) and math.isnan(v):
                    row[k] = None

        return JSONResponse({
            "file_id": file_id,
            "filename": file.filename,
            "rows": len(df),
            "columns": list(df.columns),
            "preview": records
        })
    except Exception as e:
        raise HTTPException(500, f"Erreur de parsing: {str(e)}")
