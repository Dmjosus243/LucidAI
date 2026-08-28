import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    # URL publique du backend (sert pour les notify/return_url CinetPay)
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lucidai.db")

    # SMTP (envoi d'emails : OTP de réinitialisation de mot de passe)
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "")

    # MaishaPay (paiement des abonnements — RDC, Mobile Money + carte)
    MAISHAPAY_PUBLIC_KEY = os.getenv("MAISHAPAY_PUBLIC_KEY", "")
    MAISHAPAY_SECRET_KEY = os.getenv("MAISHAPAY_SECRET_KEY", "")
    # 0 = SandBox (test), 1 = Live (production)
    MAISHAPAY_GATEWAY_MODE = int(os.getenv("MAISHAPAY_GATEWAY_MODE", "0"))

config = Config()