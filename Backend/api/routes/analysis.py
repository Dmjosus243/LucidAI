from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
import logging
import datetime
import io
import pandas as pd

from database import get_db, Analysis, supabase # supabase doit être importé de ta config
from agents.orchestrator import orchestrator
from api.dependencies import get_current_user
from api.audit import log_action
from database import Profile

logger = logging.getLogger(__name__)

router = APIRouter()

def run_analysis_task(analysis_id: str, file_path: str, filename: str):
    """
    Tâche exécutée en arrière-plan (Background Task).
    Elle télécharge le fichier depuis Supabase, l'analyse avec LangGraph,
    puis met à jour la base de données PostgreSQL.
    """
    # Note: On doit instancier une nouvelle session DB pour la tâche asynchrone
    from database import SessionLocal
    db = SessionLocal()
    
    try:
        # 1. Télécharger le fichier CSV depuis Supabase Storage
        response = supabase.storage.from_("documents_comptables").download(file_path)
        
        # 2. Charger dans Pandas
        df = pd.read_csv(io.BytesIO(response))
        
        # 3. Exécuter le graphe d'agents LangGraph (synchronement dans ce thread séparé)
        result = orchestrator.run(df, filename)
        
        # 4. Mettre à jour le statut dans la BDD (PostgreSQL)
        db_analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if db_analysis:
            db_analysis.status = "done"
            db_analysis.risk_score = result.get("risk_score", 0.0)
            db_analysis.anomalies = result.get("anomalies", [])
            db_analysis.report_path = result.get("report_path", "")
            db_analysis.completed_at = datetime.datetime.utcnow()
            db.commit()

    except Exception as e:
        logger.error(f"Erreur d'analyse pour {analysis_id} : {str(e)}")
        db_analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if db_analysis:
            db_analysis.status = "error"
            db.commit()
    finally:
        db.close()


@router.post("/analyze/{file_id}")
async def start_analysis(
    file_id: str,
    background_tasks: BackgroundTasks, # Injection du gestionnaire de tâches FastAPI
    request: Request = None,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    # 1. Vérifier si le fichier existe dans notre base de données (au lieu de temp_storage)
    # Remplacer 'OcrDocument' par le nom exact de ton modèle SQLAlchemy qui stocke l'upload
    # doc = db.query(OcrDocument).filter(OcrDocument.id == file_id, OcrDocument.organization_id == user.organization_id).first()
    # Si ton modèle upload n'est pas encore prêt, tu peux simuler en construisant le chemin:
    filename = f"fichier_{file_id}.csv" 
    storage_path = f"{user.organization_id}/{file_id}.csv" 
    
    analysis_id = str(uuid.uuid4())
    
    # 2. Créer l'enregistrement de l'analyse avec statut "processing"
    db_analysis = Analysis(
        id=analysis_id,
        user_id=user.id,
        organization_id=user.organization_id, # Isolation Multi-tenant !
        file_id=file_id,
        filename=filename,
        status="processing"
    )
    db.add(db_analysis)
    db.commit()

    log_action(
        db, str(user.id), "analysis.start",
        {"filename": filename, "analysis_id": analysis_id},
        request.client.host if request and request.client else None,
    )
    
    # 3. Déléguer le traitement long à BackgroundTasks
    background_tasks.add_task(run_analysis_task, analysis_id, storage_path, filename)
    
    # 4. Retourner immédiatement 202 Accepted au Frontend React
    return {"analysis_id": analysis_id, "status": "processing", "message": "Analyse démarrée en arrière-plan"}

@router.get("/results/{analysis_id}")
async def get_results(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    # Lecture exclusive depuis la base de données (plus de analysis_storage)
    db_analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.organization_id == user.organization_id # Isolation !
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
        return {"status": "processing"}
    else:
        return {"status": db_analysis.status, "error": "Une erreur est survenue lors de l'analyse"}

@router.get("/history")
async def get_history(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
):
    # Historique filtré par organisation
    analyses = (
        db.query(Analysis)
        .filter(Analysis.organization_id == user.organization_id)
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