from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from database import get_db, Profile, Organization
from api.dependencies import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user: dict

@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
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
        role="admin",
    )
    db.add(user)
    db.commit()

    token = create_access_token(user_id)
    return AuthResponse(
        token=token,
        user={"id": user_id, "email": req.email, "full_name": req.full_name, "role": "admin"}
    )

@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Profile).filter(Profile.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(401, "Email ou mot de passe incorrect")

    token = create_access_token(str(user.id))
    return AuthResponse(
        token=token,
        user={"id": str(user.id), "email": user.email, "full_name": user.full_name, "role": user.role}
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
