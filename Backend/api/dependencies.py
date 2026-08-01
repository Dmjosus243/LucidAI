from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.hash import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db, Profile, Organization
import uuid

from config import config

security = HTTPBearer()
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {"sub": user_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Profile:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    user = db.query(Profile).filter(Profile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    if user.is_active is False:
        raise HTTPException(status_code=403, detail="Compte désactivé")
    return user

def is_super_admin(user: Profile) -> bool:
    return user.role == "super_admin"

def is_org_admin(user: Profile) -> bool:
    return user.role in ("super_admin", "org_admin", "admin")

def is_manager_or_above(user: Profile) -> bool:
    return user.role in ("super_admin", "org_admin", "admin", "manager")

def require_org_admin(user: Profile) -> None:
    if not is_org_admin(user):
        raise HTTPException(status_code=403, detail="Réservé à l'administrateur de l'organisation")

def require_super_admin(user: Profile) -> None:
    if not is_super_admin(user):
        raise HTTPException(status_code=403, detail="Réservé à l'administrateur de la plateforme")
