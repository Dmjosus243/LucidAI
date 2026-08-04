from sqlalchemy import create_engine, Column, String, Integer, Float, JSON, DateTime, Text, ForeignKey, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import config
import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

# Récupérer l'URL depuis le .env (via config.py)
SQLALCHEMY_DATABASE_URL = config.DATABASE_URL

# Connexion à la base (avec SSL pour Supabase)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=(
        {"sslmode": "require", "options": "-c statement_timeout=15000"}
        if "supabase" in SQLALCHEMY_DATABASE_URL
        else {}
    ),
)

# Session locale pour les requêtes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()

# ---------- MODÈLES (TABLES) ----------

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subscription_tier = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    users = relationship("Profile", back_populates="organization")
    analyses = relationship("Analysis", back_populates="organization")

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="auditor")
    is_active = Column(Boolean, default=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    organization = relationship("Organization", back_populates="users")
    analyses = relationship("Analysis", back_populates="user")

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    file_id = Column(String)
    filename = Column(String)
    status = Column(String, default="pending")
    risk_score = Column(Float, default=0.0)
    anomalies = Column(JSON, default=[])
    report_path = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("Profile", back_populates="analyses")
    organization = relationship("Organization", back_populates="analyses")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    action = Column(String, nullable=False)
    details = Column(JSON, default={})
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("Profile")

# ---------- FONCTION D'INITIALISATION ----------
def init_db():
    """
    Crée les tables et applique les migrations minimales.
    """
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[WARN] create_all: {e}")

    try:
        # Migrations robustes : pas d'introspection (évite les timeouts sur le pooler Supabase)
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey"))
            conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email VARCHAR"))
            conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS hashed_password VARCHAR"))
            conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
            conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS invited_by UUID"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP"))
            conn.commit()
        print("[OK] Base de donnees connectee avec succes.")
    except Exception as e:
        print(f"[ERREUR] Connexion a la base : {e}")

# ---------- FONCTION POUR OBTENIR UNE SESSION ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()