from sqlalchemy import create_engine, Column, String, Integer, Float, JSON, DateTime, Text, ForeignKey, Boolean, text, inspect as sqlalchemy_inspect
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

# ---------- FONCTION D'INITIALISATION ----------
def init_db():
    """
    Crée les tables et ajoute les colonnes manquantes si nécessaire.
    """
    try:
        Base.metadata.create_all(bind=engine)
        
        # Migration : ajouter les colonnes manquantes si la table existe déjà
        with engine.connect() as conn:
            inspector = sqlalchemy_inspect(engine)
            
            # Ajouter email + hashed_password à profiles si absents
            if "profiles" in inspector.get_table_names():
                profiles_cols = {c["name"] for c in inspector.get_columns("profiles")}
                if "email" not in profiles_cols:
                    conn.execute(text("ALTER TABLE profiles ADD COLUMN email VARCHAR UNIQUE NOT NULL DEFAULT ''"))
                if "hashed_password" not in profiles_cols:
                    conn.execute(text("ALTER TABLE profiles ADD COLUMN hashed_password VARCHAR NOT NULL DEFAULT ''"))
            
            # Ajouter completed_at à analyses si absent
            if "analyses" in inspector.get_table_names():
                analyses_cols = {c["name"] for c in inspector.get_columns("analyses")}
                if "completed_at" not in analyses_cols:
                    conn.execute(text("ALTER TABLE analyses ADD COLUMN completed_at TIMESTAMP"))
            
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