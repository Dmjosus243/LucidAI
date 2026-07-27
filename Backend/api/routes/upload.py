from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import io
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
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
        
        # Nettoyer les colonnes
        df.columns = df.columns.str.strip().str.lower()
        
        # Stockage temporaire en mémoire (pour la démo)
        # Dans la vraie vie, on sauvegarderait en BDD
        from main import temp_storage
        temp_storage[file_id] = {"df": df, "filename": file.filename}
        
        return JSONResponse({
            "file_id": file_id,
            "filename": file.filename,
            "rows": len(df),
            "columns": list(df.columns),
            "preview": df.head(5).to_dict(orient="records")
        })
    except Exception as e:
        raise HTTPException(500, f"Erreur de parsing: {str(e)}")