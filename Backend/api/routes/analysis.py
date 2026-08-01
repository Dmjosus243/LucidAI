from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import uuid
import asyncio
import logging
import datetime

from database import get_db, Analysis
from storage import temp_storage, analysis_storage
from agents.orchestrator import orchestrator
from api.dependencies import get_current_user
from api.audit import log_action
from database import Profile

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze/{file_id}")
async def start_analysis(
    file_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if file_id not in temp_storage:
        raise HTTPException(404, "Fichier non trouvé ou expiré")
    
    data = temp_storage[file_id]
    analysis_id = str(uuid.uuid4())
    
    db_analysis = Analysis(
        id=analysis_id,
        user_id=user.id,
        organization_id=user.organization_id,
        file_id=file_id,
        filename=data["filename"],
        status="processing"
    )
    db.add(db_analysis)
    db.commit()

    log_action(
        db, str(user.id), "analysis.start",
        {"filename": data["filename"], "analysis_id": analysis_id},
        request.client.host if request and request.client else None,
    )
    
    try:
        result = await asyncio.to_thread(orchestrator.run, data["df"], data["filename"])
        
        db_analysis.status = "done"
        db_analysis.risk_score = result.get("risk_score", 0.0)
        db_analysis.anomalies = result.get("anomalies", [])
        db_analysis.report_path = result.get("report_path", "")
        db_analysis.completed_at = datetime.datetime.utcnow()
        db.commit()
        
        analysis_storage[analysis_id] = {
            "status": "done",
            "result": result,
            "filename": data["filename"]
        }
        
        del temp_storage[file_id]
        
        return {"analysis_id": analysis_id, "status": "processing"}
        
    except Exception as e:
        db_analysis.status = "error"
        db.commit()
        logger.error("Erreur d'analyse pour %s : %s", file_id, e)
        raise HTTPException(500, f"Erreur d'analyse: {str(e)}")

@router.get("/results/{analysis_id}")
async def get_results(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if analysis_id in analysis_storage:
        data = analysis_storage[analysis_id]
        if data["status"] == "done":
            result = data["result"]
            return {
                "status": "done",
                "risk_score": result.get("risk_score", 0),
                "anomalies": result.get("anomalies", []),
                "report_path": result.get("report_path", ""),
                "filename": data.get("filename", "")
            }
        else:
            return {"status": "pending"}
    
    db_analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == user.id
    ).first()
    if not db_analysis:
        raise HTTPException(404, "Analyse non trouvée")
    
    if db_analysis.status == "done":
        return {
            "status": "done",
            "risk_score": db_analysis.risk_score,
            "anomalies": db_analysis.anomalies,
            "report_path": db_analysis.report_path,
            "filename": db_analysis.filename
        }
    elif db_analysis.status == "processing":
        return {"status": "pending"}
    else:
        return {"status": db_analysis.status, "error": "Une erreur est survenue"}

@router.get("/history")
async def get_history(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
):
    analyses = (
        db.query(Analysis)
        .filter(Analysis.user_id == user.id)
        .order_by(Analysis.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(a.id),
            "filename": a.filename,
            "status": a.status,
            "risk_score": a.risk_score,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in analyses
    ]
