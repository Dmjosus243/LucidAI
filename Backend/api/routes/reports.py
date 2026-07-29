from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from database import get_db, Analysis
from storage import analysis_storage
from api.dependencies import get_current_user
from database import Profile

router = APIRouter()

@router.get("/report/{analysis_id}/pdf")
async def download_report(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
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

    db_analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == user.id
    ).first()
    if not db_analysis:
        raise HTTPException(404, "Analyse non trouvée")
    if db_analysis.status != "done":
        raise HTTPException(400, "Analyse pas encore terminée")

    report_path = db_analysis.report_path
    if not report_path or not os.path.exists(report_path):
        raise HTTPException(404, "Rapport PDF non trouvé sur le serveur")

    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"lucidai_audit_{analysis_id}.pdf"
    )
