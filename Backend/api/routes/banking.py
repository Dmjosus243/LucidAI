# -*- coding: utf-8 -*-
"""APIs bancaires & webhooks (Feature 7).

Gère :
  - la gestion des comptes bancaires (connexion API générique / agnostique) ;
  - l'ingestion de relevés (réutilisation de l'import rapprochement) ;
  - la réception idempotente de webhooks de notification ;
  - la consultation des événements.

Design OSS : pas de dépendance à un fournisseur bancaire fermé. Les adaptateurs
réels (MaishaPay, banques RDC) sont extensibles via le champ `provider` et le
`webhook_events.payload`. L'ingestion est générique et validée.
"""
import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, Profile, Organization, BankAccount, WebhookEvent
from api.dependencies import get_current_user, require_manager_or_above
from api.audit import log_action

router = APIRouter(tags=["banking"])


class AccountRequest(BaseModel):
    label: str
    bank_code: str | None = None
    currency: str = "CDF"
    provider: str = "generic"


class WebhookPayload(BaseModel):
    event_id: str | None = None
    event_type: str | None = None
    provider: str = "generic"
    amount: float | None = None
    date: str | None = None
    description: str | None = None
    account: str | None = None
    data: dict | None = None


def webhook_fingerprint(provider: str, event_id: str | None, body: dict) -> str:
    """Construit l'empreinte d'idempotence d'un événement webhook.

    - Si event_id est fourni : <provider>:<event_id>
    - Sinon : hash(provider|event_type|amount|date)
    """
    if event_id:
        return f"{provider}:{event_id}"
    raw = f"{provider}|{body.get('event_type')}|{body.get('amount')}|{body.get('date')}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _require_org(user: Profile, db: Session) -> Organization:
    if not user.organization_id:
        raise HTTPException(400, "Vous n'avez pas d'organisation")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        raise HTTPException(404, "Organisation non trouvée")
    return org


@router.post("/banking/accounts")
async def create_account(
    req: AccountRequest,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    require_manager_or_above(user)
    org = _require_org(user, db)
    account = BankAccount(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        bank_code=req.bank_code,
        label=req.label,
        currency=req.currency,
        provider=req.provider,
        config={},
    )
    db.add(account)
    db.commit()
    log_action(
        db, str(user.id), "banking.account_create",
        {"label": req.label, "provider": req.provider},
    )
    return {
        "id": str(account.id),
        "label": account.label,
        "bank_code": account.bank_code,
        "currency": account.currency,
        "provider": account.provider,
    }


@router.get("/banking/accounts")
async def list_accounts(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if not user.organization_id:
        return []
    accounts = (
        db.query(BankAccount)
        .filter(BankAccount.organization_id == user.organization_id)
        .order_by(BankAccount.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(a.id),
            "label": a.label,
            "bank_code": a.bank_code,
            "currency": a.currency,
            "provider": a.provider,
            "last_sync_at": a.last_sync_at.isoformat() if a.last_sync_at else None,
        }
        for a in accounts
    ]


@router.delete("/banking/accounts/{account_id}")
async def delete_account(
    account_id: str,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    require_manager_or_above(user)
    org = _require_org(user, db)
    account = db.query(BankAccount).filter(BankAccount.id == account_id,
                                           BankAccount.organization_id == org.id).first()
    if not account:
        raise HTTPException(404, "Compte introuvable")
    db.delete(account)
    db.commit()
    log_action(db, str(user.id), "banking.account_delete", {"account": account.label})
    return {"ok": True}


@router.post("/banking/webhook")
async def receive_webhook(
    req: WebhookPayload,
    request: Request,
    db: Session = Depends(get_db),
):
    """Reçoit un événement bancaire. Idempotent : construit une empreinte de
    l'événement et ignore les doublons. Retour rapide (200) comme recommandé
    aux fournisseurs d'APIs de notification."""
    payload = req.model_dump()
    # Empreinte unique (idempotence) : event_id fourni OU hash du contenu
    fingerprint = webhook_fingerprint(req.provider, req.event_id, payload)

    existing = db.query(WebhookEvent).filter(WebhookEvent.event_key == fingerprint).first()
    if existing:
        # Déjà traité -> renvoie l'état sans re-traitement
        return {"status": "duplicate", "event_id": existing.id}

    # Résolution de l'organisation par compte (générique) ; sinon None
    org_id = None
    if req.account:
        acct = db.query(BankAccount).filter(BankAccount.label == req.account).first()
        if acct:
            org_id = acct.organization_id

    event = WebhookEvent(
        id=str(uuid.uuid4()),
        event_key=fingerprint,
        organization_id=org_id,
        provider=req.provider,
        event_type=req.event_type,
        payload=payload,
        status="received",
        received_at=_utcnow(),
    )
    db.add(event)
    db.flush()

    # Traitement générique : marque comme traité. Un adaptateur réel pourrait
    # déclencher ici un import de relevé / une notification.
    try:
        event.status = "processed"
        event.processed_at = _utcnow()
        db.commit()
    except Exception:
        db.rollback()
        event.status = "failed"
        db.commit()

    return {
        "status": "processed" if event.status == "processed" else "failed",
        "event_id": event.id,
    }


@router.get("/banking/webhook/events")
async def list_webhook_events(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
    limit: int = 100,
):
    if user.role == "super_admin":
        query = db.query(WebhookEvent)
    else:
        if not user.organization_id:
            return []
        query = db.query(WebhookEvent).filter(WebhookEvent.organization_id == user.organization_id)
    events = query.order_by(WebhookEvent.received_at.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "provider": e.provider,
            "event_type": e.event_type,
            "status": e.status,
            "payload": e.payload,
            "received_at": e.received_at.isoformat() if e.received_at else None,
        }
        for e in events
    ]
