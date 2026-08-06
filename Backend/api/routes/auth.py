from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import secrets
import datetime

from database import get_db, Profile, Organization, PasswordReset
from api.dependencies import hash_password, verify_password, create_access_token, get_current_user
from api.audit import log_action
from api.mailer import send_email
from config import config

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

class AuthResponse(BaseModel):
    token: str
    user: dict

@router.post("/register")
async def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    existing = db.query(Profile).filter(Profile.email == req.email).first()
    if existing:
        raise HTTPException(400, "Email déjà utilisé")

    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())

    org = Organization(id=org_id, name=f"{req.full_name}'s Organization")
    db.add(org)

    user = Profile(
        id=user_id,
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        organization_id=org_id,
        role="org_admin",
        is_active=True,
    )
    db.add(user)
    db.commit()

    log_action(db, user_id, "register", {"email": req.email}, request.client.host if request.client else None)

    token = create_access_token(user_id)
    return AuthResponse(
        token=token,
        user={"id": user_id, "email": req.email, "full_name": req.full_name, "role": "org_admin", "organization_id": org_id}
    )

@router.post("/login")
async def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(Profile).filter(Profile.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(401, "Email ou mot de passe incorrect")
    if user.is_active is False:
        raise HTTPException(403, "Compte désactivé")

    log_action(db, str(user.id), "login", {"email": req.email}, request.client.host if request.client else None)

    token = create_access_token(str(user.id))
    return AuthResponse(
        token=token,
        user={"id": str(user.id), "email": user.email, "full_name": user.full_name, "role": user.role, "organization_id": str(user.organization_id) if user.organization_id else None}
    )

@router.get("/me")
async def get_me(user: Profile = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "organization_id": str(user.organization_id) if user.organization_id else None,
    }

@router.post("/forgot-password")
async def forgot_password(
    req: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(Profile).filter(Profile.email == req.email.lower().strip()).first()
    if not user:
        # Réponse identique pour éviter de révéler si l'email existe
        return {"ok": True}

    # Invalider les anciens OTP de cet utilisateur
    db.query(PasswordReset).filter(
        PasswordReset.user_id == user.id,
        PasswordReset.used.is_(False)
    ).update({"used": True})
    db.commit()

    otp = f"{secrets.randbelow(1000000):06d}"
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)

    reset = PasswordReset(
        id=str(uuid.uuid4()),
        user_id=user.id,
        otp=otp,
        expires_at=expires_at,
        used=False,
    )
    db.add(reset)
    db.commit()

    log_action(
        db, str(user.id), "auth.forgot_password",
        {"email": req.email},
        request.client.host if request.client else None,
    )

    send_email(
        to=req.email,
        subject="Réinitialisation de votre mot de passe LucidAI",
        text_body=(
            f"Bonjour {user.full_name or ''},\n\n"
            f"Votre code de réinitialisation est : {otp}\n\n"
            f"Ce code est valable 30 minutes. Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n\n"
            f"L'équipe LucidAI"
        ),
        html_body=(
            f"<p>Bonjour <strong>{user.full_name or ''}</strong>,</p>"
            f"<p>Votre code de réinitialisation est :</p>"
            f"<p style='font-size:28px;font-weight:bold;letter-spacing:6px'>{otp}</p>"
            f"<p>Ce code est <strong>valable 30 minutes</strong>. Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>"
            f"<p>L'équipe LucidAI</p>"
        ),
    )

    return {"ok": True}

@router.post("/reset-password")
async def reset_password(
    req: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(Profile).filter(Profile.email == req.email.lower().strip()).first()
    if not user:
        raise HTTPException(404, "Email introuvable")

    now = datetime.datetime.utcnow()
    reset = (
        db.query(PasswordReset)
        .filter(
            PasswordReset.user_id == user.id,
            PasswordReset.used.is_(False),
            PasswordReset.otp == req.otp.strip(),
        )
        .order_by(PasswordReset.created_at.desc())
        .first()
    )
    if not reset:
        raise HTTPException(400, "Code OTP invalide")
    if reset.expires_at < now:
        raise HTTPException(400, "Le code OTP a expiré (30 minutes)")
    if len(req.new_password) < 6:
        raise HTTPException(400, "Le mot de passe doit contenir au moins 6 caractères")

    user.hashed_password = hash_password(req.new_password)
    reset.used = True
    db.commit()

    log_action(
        db, str(user.id), "auth.reset_password",
        {"email": req.email},
        request.client.host if request.client else None,
    )

    return {"ok": True, "message": "Mot de passe réinitialisé avec succès"}
