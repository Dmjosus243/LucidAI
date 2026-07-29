from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from storage import analysis_storage

router = APIRouter()

@router.get("/report/{analysis_id}/pdf")
async def download_report(analysis_id: str):
    # 1. Vérifier en mémoire (pour les analyses récentes)
    if analysis_id in analysis_storage:
        data = analysis_storage[analysis_id]
        if data["status"] == "done":
            report_path = data.get("result", {}).get("report_path", "")
            if report_path and os.path.exists(report_path):
                return FileResponse(
                    report_path,
                    media_type="application/pdf",
                    filename=f"lucidai_audit_{analysis_id}.pdf"
                )
            else:
                raise HTTPException(404, "Rapport PDF non trouvé sur le serveur")
    
    # 2. Sinon, on pourrait chercher en base, mais pour le MVP on s'arrête là
    raise HTTPException(404, "Analyse non trouvée ou rapport non généré")