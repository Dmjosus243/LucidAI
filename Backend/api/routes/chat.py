# -*- coding: utf-8 -*-
"""Routes de l'assistant conversationnel (Feature 5)."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, Profile, Organization, ChatSession, ChatMessage, JournalEntry, Analysis
from api.dependencies import get_current_user
from engine.recommender import answer

router = APIRouter(tags=["chat"])


class CreateSessionRequest(BaseModel):
    title: str | None = None


class SendMessageRequest(BaseModel):
    content: str


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _require_org(user: Profile, db: Session) -> Organization:
    if not user.organization_id:
        raise HTTPException(400, "Vous n'avez pas d'organisation")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        raise HTTPException(404, "Organisation non trouvée")
    return org


def _gather_org_data(db: Session, org_id) -> dict:
    """Rassemble les données de l'organisation pour le contexte assistant."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    entries = db.query(JournalEntry).filter(JournalEntry.organization_id == org_id).all()
    analyses = db.query(Analysis).filter(Analysis.organization_id == org_id).all()
    anomalies = []
    for a in analyses:
        anomalies.extend(a.anomalies or [])
    return {
        "org_name": org.name if org else "",
        "entries": [
            {
                "source": e.source,
                "lines": e.lines or [],
                "date": e.date,
            }
            for e in entries
        ],
        "analyses": [
            {"risk_score": a.risk_score, "status": a.status}
            for a in analyses
        ],
        "anomalies": anomalies,
    }


@router.post("/chat/sessions")
async def create_session(
    req: CreateSessionRequest,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    org = _require_org(user, db)
    session = ChatSession(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        user_id=user.id,
        title=req.title or "Nouvelle conversation",
    )
    db.add(session)
    db.commit()
    return {
        "id": str(session.id),
        "title": session.title,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


@router.get("/chat/sessions")
async def list_sessions(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if user.role == "super_admin":
        sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).limit(50).all()
    else:
        if not user.organization_id:
            return []
        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.organization_id == user.organization_id)
            .order_by(ChatSession.created_at.desc())
            .limit(50)
            .all()
        )
    return [
        {
            "id": str(s.id),
            "title": s.title,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]


@router.post("/chat/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    req: SendMessageRequest,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session introuvable")
    if user.role != "super_admin" and session.organization_id != user.organization_id:
        raise HTTPException(403, "Session non autorisée")

    content = req.content.strip()
    if not content:
        raise HTTPException(400, "Message vide")

    # Message utilisateur
    db.add(ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role="user",
        content=content,
        created_at=_utcnow(),
    ))
    db.flush()

    # Réponse
    try:
        org_data = _gather_org_data(db, session.organization_id) if session.organization_id else {}
    except Exception:
        org_data = {}
    result = answer(content, org_data)

    assistant_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role="assistant",
        content=result["text"],
        context={"mode": result["mode"]},
        created_at=_utcnow(),
    )
    db.add(assistant_msg)
    db.commit()

    return {
        "user_message": {"role": "user", "content": content},
        "assistant_message": {
            "id": str(assistant_msg.id),
            "role": "assistant",
            "content": assistant_msg.content,
            "mode": result["mode"],
        },
    }


@router.get("/chat/sessions/{session_id}/messages")
async def list_messages(
    session_id: str,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session introuvable")
    if user.role != "super_admin" and session.organization_id != user.organization_id:
        raise HTTPException(403, "Session non autorisée")
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "mode": (m.context or {}).get("mode") if m.context else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in msgs
    ]
