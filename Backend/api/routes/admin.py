from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
import uuid

from database import get_db, Profile, Organization, Analysis, AuditLog
from api.dependencies import (
    get_current_user,
    hash_password,
    require_org_admin,
    require_super_admin,
    is_org_admin,
)
from api.audit import log_action

router = APIRouter(tags=["admin"])

class InviteRequest(BaseModel):
    email: str
    full_name: str
    role: str = "auditor"
    password: str | None = None

class UpdateUserRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    full_name: str | None = None

class UpdateOrgRequest(BaseModel):
    name: str | None = None
    subscription_tier: str | None = None

ALLOWED_ROLES = ("super_admin", "org_admin", "manager", "auditor", "admin")
ALLOWED_TIERS = ("free", "pro", "enterprise")

def serialize_user(u: Profile) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role,
        "is_active": u.is_active is not False,
        "organization_id": str(u.organization_id) if u.organization_id else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }

@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if user.role == "super_admin":
        users = db.query(Profile).order_by(Profile.created_at.desc()).all()
    else:
        if not user.organization_id:
            return []
        users = db.query(Profile).filter(Profile.organization_id == user.organization_id).all()
    return [serialize_user(u) for u in users]

@router.post("/users")
async def invite_user(
    req: InviteRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    require_org_admin(user)
    if not user.organization_id:
        raise HTTPException(400, "Vous n'avez pas d'organisation")
    if req.role not in ALLOWED_ROLES:
        raise HTTPException(400, f"Rôle invalide. Choisissez parmi : {', '.join(ALLOWED_ROLES)}")

    existing = db.query(Profile).filter(Profile.email == req.email).first()
    if existing:
        raise HTTPException(400, "Cet email est déjà utilisé")

    temp_password = req.password or uuid.uuid4().hex[:10]
    member = Profile(
        id=str(uuid.uuid4()),
        organization_id=user.organization_id,
        email=req.email,
        hashed_password=hash_password(temp_password),
        full_name=req.full_name,
        role=req.role,
        is_active=True,
        invited_by=user.id,
    )
    db.add(member)
    db.commit()

    log_action(
        db, str(user.id), "user.invite",
        {"email": req.email, "role": req.role},
        request.client.host if request.client else None,
    )

    result = serialize_user(member)
    result["temporary_password"] = temp_password
    return result

@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    req: UpdateUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    target = db.query(Profile).filter(Profile.id == user_id).first()
    if not target:
        raise HTTPException(404, "Utilisateur non trouvé")

    if user.role != "super_admin":
        require_org_admin(user)
        if target.organization_id != user.organization_id:
            raise HTTPException(403, "Cet utilisateur n'appartient pas à votre organisation")

    changes = []
    if req.role is not None:
        if req.role not in ALLOWED_ROLES:
            raise HTTPException(400, f"Rôle invalide. Choisissez parmi : {', '.join(ALLOWED_ROLES)}")
        if user.role != "super_admin" and req.role == "super_admin":
            raise HTTPException(403, "Impossible d'attribuer le rôle super_admin")
        target.role = req.role
        changes.append(f"role -> {req.role}")

    if req.is_active is not None:
        if target.id == user.id:
            raise HTTPException(400, "Vous ne pouvez pas modifier votre propre statut")
        target.is_active = req.is_active
        changes.append("désactivé" if not req.is_active else "activé")

    if req.full_name is not None:
        target.full_name = req.full_name
        changes.append(f"nom -> {req.full_name}")

    db.commit()
    log_action(
        db, str(user.id), "user.update",
        {"target": target.email, "changes": changes},
        request.client.host if request.client else None,
    )
    return serialize_user(target)

@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    target = db.query(Profile).filter(Profile.id == user_id).first()
    if not target:
        raise HTTPException(404, "Utilisateur non trouvé")
    if target.id == user.id:
        raise HTTPException(400, "Vous ne pouvez pas désactiver votre propre compte")
    if target.role == "super_admin" and user.role == "super_admin":
        raise HTTPException(400, "Impossible de désactiver un super_admin")

    if user.role != "super_admin":
        require_org_admin(user)
        if target.organization_id != user.organization_id:
            raise HTTPException(403, "Cet utilisateur n'appartient pas à votre organisation")

    target.is_active = False
    db.commit()
    log_action(
        db, str(user.id), "user.deactivate", {"target": target.email},
        request.client.host if request.client else None,
    )
    return {"ok": True}

@router.get("/organizations/me")
async def get_my_organization(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if not user.organization_id:
        return None
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        raise HTTPException(404, "Organisation non trouvée")
    member_count = db.query(Profile).filter(Profile.organization_id == org.id).count()
    return {
        "id": str(org.id),
        "name": org.name,
        "subscription_tier": org.subscription_tier,
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "member_count": member_count,
    }

@router.patch("/organizations/me")
async def update_my_organization(
    req: UpdateOrgRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    require_org_admin(user)
    if not user.organization_id:
        raise HTTPException(400, "Vous n'avez pas d'organisation")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        raise HTTPException(404, "Organisation non trouvée")

    changes = []
    if req.name is not None:
        org.name = req.name
        changes.append(f"nom -> {req.name}")
    if req.subscription_tier is not None:
        if req.subscription_tier not in ALLOWED_TIERS:
            raise HTTPException(400, f"Niveau invalide. Choisissez parmi : {', '.join(ALLOWED_TIERS)}")
        org.subscription_tier = req.subscription_tier
        changes.append(f"abonnement -> {req.subscription_tier}")

    db.commit()
    log_action(
        db, str(user.id), "org.update", {"changes": changes},
        request.client.host if request.client else None,
    )
    return get_my_organization(db=db, user=user)

@router.get("/analyses/org")
async def get_org_analyses(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if user.role not in ("super_admin", "org_admin", "admin", "manager"):
        raise HTTPException(403, "Réservé au manager ou à l'administrateur")
    if not user.organization_id:
        return []
    analyses = (
        db.query(Analysis)
        .filter(Analysis.organization_id == user.organization_id)
        .order_by(Analysis.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": str(a.id),
            "filename": a.filename,
            "status": a.status,
            "risk_score": a.risk_score,
            "user_id": str(a.user_id) if a.user_id else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in analyses
    ]

@router.get("/audit-logs")
async def get_audit_logs(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
    limit: int = 100,
):
    query = db.query(AuditLog)
    if user.role != "super_admin":
        require_org_admin(user)
        member_ids = [
            m.id for m in db.query(Profile).filter(Profile.organization_id == user.organization_id).all()
        ]
        if not member_ids:
            return []
        query = query.filter(AuditLog.user_id.in_(member_ids))
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(l.id),
            "user_id": str(l.user_id) if l.user_id else None,
            "action": l.action,
            "details": l.details,
            "ip_address": l.ip_address,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]

@router.get("/admin/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    require_super_admin(user)
    total_users = db.query(Profile).count()
    total_orgs = db.query(Organization).count()
    total_analyses = db.query(Analysis).count()
    avg_risk = db.query(func.avg(Analysis.risk_score)).scalar() or 0

    by_tier = db.query(Organization.subscription_tier, func.count()).group_by(Organization.subscription_tier).all()
    by_role = db.query(Profile.role, func.count()).group_by(Profile.role).all()

    return {
        "total_users": total_users,
        "total_organizations": total_orgs,
        "total_analyses": total_analyses,
        "avg_risk_score": round(float(avg_risk), 2),
        "organizations_by_tier": {t or "free": c for t, c in by_tier},
        "users_by_role": {r or "auditor": c for r, c in by_role},
    }
