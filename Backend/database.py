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
# pool_pre_ping : vérifie la connexion avant usage (les connexions inactives
# sont souvent coupées par le pooler Supabase) -> évite les 500 intermittents
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=(
        {"sslmode": "require", "options": "-c statement_timeout=15000"}
        if "supabase" in SQLALCHEMY_DATABASE_URL
        else {}
    ),
    pool_pre_ping=True,
    pool_recycle=300,
    pool_timeout=10,
    max_overflow=5,
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
    subscription_status = Column(String, default="inactive")
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
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

class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    otp = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# ---------- MODÈLES V2 (7 fonctionnalités) ----------

class OCRDocument(Base):
    """Documents soumis à l'OCR + validation humaine (F1)."""
    __tablename__ = "ocr_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    filename = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending / validated / rejected
    engine = Column(String, default="transparent")  # transparent / tesseract / paddle
    extracted_json = Column(JSON, default=[])
    validated_json = Column(JSON, nullable=True)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    validated_at = Column(DateTime, nullable=True)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)

class JournalEntry(Base):
    """Écritures comptables issues de l'OCR / rapprochement / prédiction (F1/F2/F3)."""
    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    entry_ref = Column(String, nullable=False)
    date = Column(String, nullable=True)
    source = Column(String, default="manuel")  # ocr / recon / predicted / manuel
    confidence = Column(Float, default=0.0)
    lines = Column(JSON, default=[])
    status = Column(String, default="pending")  # pending / validated / rejected
    validated_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BankAccount(Base):
    """Comptes bancaires (F2/F7)."""
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    bank_code = Column(String, nullable=True)
    label = Column(String, nullable=True)
    currency = Column(String, default="CDF")
    provider = Column(String, default="generic")
    last_sync_at = Column(DateTime, nullable=True)
    config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BankStatement(Base):
    """Relevés bancaires bruts importés (F2/F7)."""
    __tablename__ = "bank_statements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=True)
    date_range = Column(String, nullable=True)
    source = Column(String, default="upload")
    raw = Column(JSON, default=[])
    imported_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ReconciliationItem(Base):
    """Pointage entre lignes de relevé et écritures (F2)."""
    __tablename__ = "reconciliation_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    statement_id = Column(UUID(as_uuid=True), ForeignKey("bank_statements.id"), nullable=True)
    statement_line = Column(JSON, default={})
    entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True)
    status = Column(String, default="unmatched")  # matched / unmatched / auto
    confidence = Column(Float, default=0.0)
    matched_at = Column(DateTime, nullable=True)
    matched_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ChatSession(Base):
    """Session de l'assistant conversationnel (F5)."""
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    title = Column(String, default="Nouvelle conversation")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ChatMessage(Base):
    """Message d'une session (F5)."""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    context = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WebhookEvent(Base):
    """Événements bancaires entrants (F7)."""
    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_key = Column(String, unique=True, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    provider = Column(String, default="generic")
    event_type = Column(String, nullable=True)
    payload = Column(JSON, default={})
    status = Column(String, default="received")  # received / processed / failed
    received_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

# ---------- FONCTION D'INITIALISATION ----------
def init_db():
    """
    Crée les tables et applique les migrations minimales.

    On utilise UNIQUEMENT du SQL brut (CREATE TABLE IF NOT EXISTS / ALTER ... IF NOT EXISTS)
    au lieu de Base.metadata.create_all() : ce dernier fait de l'introspection
    (has_table) qui est très lente / se bloque sur le pooler Supabase.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id UUID PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    subscription_tier VARCHAR DEFAULT 'free',
                    subscription_status VARCHAR DEFAULT 'inactive',
                    stripe_customer_id VARCHAR,
                    stripe_subscription_id VARCHAR,
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id UUID PRIMARY KEY,
                    organization_id UUID REFERENCES public.organizations(id),
                    email VARCHAR UNIQUE NOT NULL,
                    hashed_password VARCHAR NOT NULL,
                    full_name VARCHAR,
                    role VARCHAR DEFAULT 'auditor',
                    is_active BOOLEAN DEFAULT TRUE,
                    invited_by UUID REFERENCES public.profiles(id),
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES public.profiles(id),
                    organization_id UUID REFERENCES public.organizations(id),
                    file_id VARCHAR,
                    filename VARCHAR,
                    status VARCHAR DEFAULT 'pending',
                    risk_score FLOAT DEFAULT 0,
                    anomalies JSON DEFAULT '[]',
                    report_path VARCHAR DEFAULT '',
                    created_at TIMESTAMP DEFAULT now(),
                    completed_at TIMESTAMP
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id UUID PRIMARY KEY,
                    user_id UUID REFERENCES public.profiles(id),
                    action VARCHAR NOT NULL,
                    details JSON DEFAULT '{}',
                    ip_address VARCHAR,
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES public.profiles(id),
                    otp VARCHAR NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ocr_documents (
                    id UUID PRIMARY KEY,
                    organization_id UUID REFERENCES public.organizations(id),
                    user_id UUID NOT NULL REFERENCES public.profiles(id),
                    filename VARCHAR NOT NULL,
                    status VARCHAR DEFAULT 'pending',
                    engine VARCHAR DEFAULT 'transparent',
                    extracted_json JSON DEFAULT '[]',
                    validated_json JSON,
                    confidence FLOAT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT now(),
                    validated_at TIMESTAMP,
                    validated_by UUID REFERENCES public.profiles(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id UUID PRIMARY KEY,
                    organization_id UUID REFERENCES public.organizations(id),
                    user_id UUID NOT NULL REFERENCES public.profiles(id),
                    entry_ref VARCHAR NOT NULL,
                    date VARCHAR,
                    source VARCHAR DEFAULT 'manuel',
                    confidence FLOAT DEFAULT 0,
                    lines JSON DEFAULT '[]',
                    status VARCHAR DEFAULT 'pending',
                    validated_by UUID REFERENCES public.profiles(id),
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    id UUID PRIMARY KEY,
                    organization_id UUID REFERENCES public.organizations(id),
                    bank_code VARCHAR,
                    label VARCHAR,
                    currency VARCHAR DEFAULT 'CDF',
                    provider VARCHAR DEFAULT 'generic',
                    last_sync_at TIMESTAMP,
                    config JSON DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS bank_statements (
                    id UUID PRIMARY KEY,
                    organization_id UUID REFERENCES public.organizations(id),
                    account_id UUID REFERENCES public.bank_accounts(id),
                    date_range VARCHAR,
                    source VARCHAR DEFAULT 'upload',
                    raw JSON DEFAULT '[]',
                    imported_by UUID REFERENCES public.profiles(id),
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS reconciliation_items (
                    id UUID PRIMARY KEY,
                    organization_id UUID REFERENCES public.organizations(id),
                    statement_id UUID REFERENCES public.bank_statements(id),
                    statement_line JSON DEFAULT '{}',
                    entry_id UUID REFERENCES public.journal_entries(id),
                    status VARCHAR DEFAULT 'unmatched',
                    confidence FLOAT DEFAULT 0,
                    matched_at TIMESTAMP,
                    matched_by UUID REFERENCES public.profiles(id),
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id UUID PRIMARY KEY,
                    organization_id UUID REFERENCES public.organizations(id),
                    user_id UUID NOT NULL REFERENCES public.profiles(id),
                    title VARCHAR DEFAULT 'Nouvelle conversation',
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id UUID PRIMARY KEY,
                    session_id UUID NOT NULL REFERENCES public.chat_sessions(id),
                    role VARCHAR NOT NULL,
                    content TEXT NOT NULL,
                    context JSON DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS webhook_events (
                    id UUID PRIMARY KEY,
                    event_key VARCHAR UNIQUE,
                    organization_id UUID REFERENCES public.organizations(id),
                    provider VARCHAR DEFAULT 'generic',
                    event_type VARCHAR,
                    payload JSON DEFAULT '{}',
                    status VARCHAR DEFAULT 'received',
                    received_at TIMESTAMP DEFAULT now(),
                    processed_at TIMESTAMP
                )
            """))
            conn.commit()
        print("[OK] Base de donnees connectee avec succes.")
    except Exception as e:
        print(f"[ERREUR] Connexion a la base : {e}")
        return

    try:
        # Migrations minimales (idempotentes)
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS subscription_status VARCHAR DEFAULT 'inactive'"))
            conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR"))
            conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR"))
            conn.execute(text("ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey"))
            conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email VARCHAR"))
            conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS hashed_password VARCHAR"))
            conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
            conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS invited_by UUID"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP"))
            conn.execute(text("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS bank_sync_enabled BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE webhook_events ADD COLUMN IF NOT EXISTS event_key VARCHAR"))
            conn.commit()
    except Exception as e:
        print(f"[WARN] Migrations : {e}")

# ---------- FONCTION POUR OBTENIR UNE SESSION ----------
import time
import logging

logger = logging.getLogger(__name__)

def _create_session(retries=3, delay=1):
    for attempt in range(retries):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            return db
        except Exception as e:
            logger.warning("DB connection attempt %d failed: %s", attempt + 1, e)
            time.sleep(delay)
    raise Exception("Impossible de se connecter à la base de données après %d tentatives" % retries)
# ---------- MODÈLES COMPTABLES ----------

class ChartOfAccount(Base):
    __tablename__ = "chart_of_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    account_number = Column(String(20), nullable=False)
    account_name = Column(String, nullable=False)
    account_type = Column(String(20))
    parent_id = Column(UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True)
    is_active = Column(String, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def get_db():
    db = None
    try:
        db = _create_session()
        yield db
    finally:
        if db:
            db.close()