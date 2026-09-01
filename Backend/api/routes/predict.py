# -*- coding: utf-8 -*-
"""Routes des écritures prédictives (Feature 3).

Génère des projets d'écritures à partir d'un journal de caisse. Les écritures
sont créées en statut "pending" et doivent être VALIDÉES par un gestionnaire
avant de devenir des écritures comptables (positionnement produit F3).
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, Profile, Organization, JournalEntry
from api.dependencies import get_current_user, require_manager_or_above, is_manager_or_above
from api.audit import log_action
from engine.prediction import predict_cash_book

router = APIRouter(tags=["predict"])


class CashOperation(BaseModel):
    date: str | None = None
    description: str = ""
    amount: float
    direction: str = "in"  # in (encaissement) | out (décaissement)


class CashBookRequest(BaseModel):
    operations: list[CashOperation]


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _require_org(user: Profile, db: Session) -> Organization:
    if not user.organization_id:
        raise HTTPException(400, "Vous n'avez pas d'organisation")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        raise HTTPException(404, "Organisation non trouvée")
    return org


@router.post("/predict/from-cash")
async def predict_from_cash(
    req: CashBookRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    require_manager_or_above(user)
    if not req.operations:
        raise HTTPException(400, "Aucune opération de caisse fournie")
    org = _require_org(user, db)

    ops = [op.model_dump() for op in req.operations]
    proposals = predict_cash_book(ops)

    created = []
    for p in proposals:
        entry = JournalEntry(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            user_id=user.id,
            entry_ref=p["entry_ref"],
            date=p["date"],
            source="predicted",
            confidence=p["confidence"],
            lines=p["lines"],
            status="pending",
        )
        db.add(entry)
        created.append({
            "id": str(entry.id),
            "entry_ref": p["entry_ref"],
            "date": p["date"],
            "confidence": p["confidence"],
            "category": p["category"],
            "description": p["description"],
            "lines": p["lines"],
            "status": "pending",
        })
    db.commit()

    log_action(
        db, str(user.id), "predict.from_cash",
        {"count": len(created), "source": "predicted"},
    )
    return {"created": created, "count": len(created)}


@router.get("/predict/pending")
async def list_pending(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    """Lister les projets d'écritures prédites (en attente + validées récentes)."""
    query = db.query(JournalEntry).filter(JournalEntry.source == "predicted")
    if user.role != "super_admin":
        if not user.organization_id:
            return []
        query = query.filter(JournalEntry.organization_id == user.organization_id)
    entries = (
        query.order_by(JournalEntry.created_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": str(e.id),
            "entry_ref": e.entry_ref,
            "date": e.date,
            "confidence": e.confidence,
            "lines": e.lines or [],
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]


def _get_scoped_entry(db: Session, user: Profile, entry_id: str) -> JournalEntry:
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Écriture introuvable")
    if user.role != "super_admin" and entry.organization_id != user.organization_id:
        raise HTTPException(403, "Écriture non autorisée")
    if entry.source != "predicted":
        raise HTTPException(400, "Cette écriture n'est pas un projet prédictif")
    return entry


@router.post("/predict/{entry_id}/validate")
async def validate_prediction(
    entry_id: str,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    """Valide/transforme un projet d'écriture prédictif en écriture comptable."""
    if not is_manager_or_above(user):
        raise HTTPException(403, "Réservé au manager ou au-dessus")
    entry = _get_scoped_entry(db, user, entry_id)
    if entry.status == "validated":
        raise HTTPException(400, "Déjà validée")

    entry.status = "validated"
    entry.validated_by = user.id
    db.commit()

    log_action(db, str(user.id), "predict.validate", {"entry_ref": entry.entry_ref})
    return {"ok": True, "entry_ref": entry.entry_ref, "status": "validated"}


@router.post("/predict/{entry_id}/reject")
async def reject_prediction(
    entry_id: str,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if not is_manager_or_above(user):
        raise HTTPException(403, "Réservé au manager ou au-dessus")
    entry = _get_scoped_entry(db, user, entry_id)
    if entry.status == "validated":
        raise HTTPException(400, "Impossible de rejeter une écriture validée")
    entry.status = "rejected"
    db.commit()
    log_action(db, str(user.id), "predict.reject", {"entry_ref": entry.entry_ref})
    return {"ok": True, "entry_ref": entry.entry_ref, "status": "rejected"}
