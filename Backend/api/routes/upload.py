import math
import io
import uuid
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
# SUPPRIME : from storage import temp_storage
from api.dependencies import get_current_user
from api.audit import log_action
from database import Profile, supabase 

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
        
        # 1. Traitement initial avec Pandas
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Standardisation des colonnes
        df.columns = df.columns.str.strip().str.lower()
        
        # 2. NOUVEAU : Conversion en CSV standardisé et envoi sur Supabase Storage
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue()
        
        # Chemin sécurisé par organisation (ex: org_id/file_id.csv)
        storage_path = f"{user.organization_id}/{file_id}.csv" 
        
        # Upload vers le bucket Supabase
        supabase.storage.from_("documents_comptables").upload(
            storage_path, 
            csv_bytes, 
            {"content-type": "text/csv"}
        )
        
        # 3. NOUVEAU : Enregistrement des métadonnées dans la BDD au lieu de la mémoire
        # new_doc = OcrDocument(id=file_id, filename=file.filename, path=storage_path, org_id=user.organization_id)
        # db.add(new_doc)
        # db.commit()

        # 4. Traçabilité des actions
        log_action(
            db, str(user.id), "file.upload",
            {"filename": file.filename, "rows": len(df)},
            request.client.host if request and request.client else None,
        )
        
        # 5. Préparation de l'aperçu (Preview) pour le Frontend React
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
        raise HTTPException(500, f"Erreur lors du traitement du fichier: {str(e)}")