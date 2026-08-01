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
        
        return JSONResponse({
            "file_id": file_id,
            "filename": file.filename,
            "rows": len(df),
            "columns": list(df.columns),
            "preview": df.head(5).to_dict(orient="records")
        })
    except Exception as e:
        raise HTTPException(500, f"Erreur de parsing: {str(e)}")
