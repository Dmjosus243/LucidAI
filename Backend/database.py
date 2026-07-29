from sqlalchemy import create_engine, Column, String, Integer, Float, JSON, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import config
import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

# Récupérer l'URL depuis le .env
SQLALCHEMY_DATABASE_URL = config.DATABASE_URL

# Connexion à la base (avec SSL pour Supabase)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"sslmode": "require"} if "supabase" in SQLALCHEMY_DATABASE_URL else {}
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
    
    # Relations
    users = relationship("Profile", back_populates="organization")
    analyses = relationship("Analysis", back_populates="organization")

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True)  # == auth.users.id
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    full_name = Column(String)
    role = Column(String, default="auditor")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relations
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
    
    # Relations
    user = relationship("Profile", back_populates="analyses")
    organization = relationship("Organization", back_populates="analyses")

# ---------- FONCTION D'INITIALISATION ----------
def init_db():
    """
    Crée les tables si elles n'existent pas déjà.
    À appeler au démarrage de l'application (dans main.py).
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables vérifiées/créées avec succès (Supabase).")
    except Exception as e:
        print(f"⚠️ Erreur lors de la création des tables : {e}")
        print("   Assurez-vous que les tables existent déjà dans Supabase.")

# ---------- FONCTION POUR OBTENIR UNE SESSION ----------
def get_db():
    """Générateur pour obtenir une session (utilisé dans les routes API)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()