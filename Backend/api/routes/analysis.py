from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid

from database import get_db, Analysis
from storage import temp_storage, analysis_storage
from agents.orchestrator import orchestrator

router = APIRouter()

@router.post("/analyze/{file_id}")
async def start_analysis(file_id: str, db: Session = Depends(get_db)):
    # Vérifier si le fichier existe en mémoire
    if file_id not in temp_storage:
        raise HTTPException(404, "Fichier non trouvé ou expiré")
    
    data = temp_storage[file_id]
    analysis_id = str(uuid.uuid4())
    
    # 1. Sauvegarder le statut "processing" en base de données
    db_analysis = Analysis(
        id=analysis_id,
        user_id="11111111-1111-1111-1111-111111111111",  # Pour le MVP, on fixe un user démo
        organization_id=None,  # On laisse vide pour le moment
        file_id=file_id,
        filename=data["filename"],
        status="processing"
    )
    db.add(db_analysis)
    db.commit()
    
    try:
        # 2. Lancer l'orchestrateur LangGraph (les 4 agents)
        result = orchestrator.run(data["df"], data["filename"])
        
        # 3. Mettre à jour la base avec les résultats
        db_analysis.status = "done"
        db_analysis.risk_score = result.get("risk_score", 0.0)
        db_analysis.anomalies = result.get("anomalies", [])
        db_analysis.report_path = result.get("report_path", "")
        db.commit()
        
        # 4. Stocker l'analyse en mémoire pour un accès rapide (optionnel)
        analysis_storage[analysis_id] = {
            "status": "done",
            "result": result,
            "filename": data["filename"]
        }
        
        # 5. Nettoyer la mémoire temporaire
        del temp_storage[file_id]
        
        return {"analysis_id": analysis_id, "status": "processing"}
        
    except Exception as e:
        db_analysis.status = "error"
        db.commit()
        raise HTTPException(500, f"Erreur d'analyse: {str(e)}")

@router.get("/results/{analysis_id}")
async def get_results(analysis_id: str, db: Session = Depends(get_db)):
    # 1. Chercher d'abord en mémoire (pour les analyses en cours)
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
    
    # 2. Sinon, chercher en base de données
    db_analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
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