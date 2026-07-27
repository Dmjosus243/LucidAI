from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from agents.orchestrator import orchestrator
from main import temp_storage
import uuid

router = APIRouter()
analysis_storage = {}

@router.post("/analyze/{file_id}")
async def start_analysis(file_id: str):
    if file_id not in temp_storage:
        raise HTTPException(404, "Fichier non trouvé")
    
    analysis_id = str(uuid.uuid4())
    data = temp_storage[file_id]
    
    # Lancer l'orchestrateur en arrière-plan (simulé)
    # Pour le MVP, on exécute de manière synchrone, mais avec un timeout pour éviter le blocage
    try:
        result = orchestrator.run(data["df"], data["filename"])
        analysis_storage[analysis_id] = {
            "status": "done",
            "result": result,
            "filename": data["filename"]
        }
        # Nettoyer le stockage temporaire
        del temp_storage[file_id]
        
        return JSONResponse({
            "analysis_id": analysis_id,
            "status": "processing"  # On simule une tâche asynchrone
        })
    except Exception as e:
        raise HTTPException(500, f"Erreur d'analyse: {str(e)}")

@router.get("/results/{analysis_id}")
async def get_results(analysis_id: str):
    if analysis_id not in analysis_storage:
        raise HTTPException(404, "Analyse non trouvée")
    
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