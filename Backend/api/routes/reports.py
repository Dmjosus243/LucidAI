from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from api.routes.analysis import analysis_storage
import os

router = APIRouter()

@router.get("/report/{analysis_id}/pdf")
async def download_report(analysis_id: str):
    if analysis_id not in analysis_storage:
        raise HTTPException(404, "Analyse non trouvée")
    
    data = analysis_storage[analysis_id]
    report_path = data.get("result", {}).get("report_path", "")
    
    if not report_path or not os.path.exists(report_path):
        raise HTTPException(404, "Rapport non généré")
    
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"lucidai_audit_{analysis_id}.pdf"
    )