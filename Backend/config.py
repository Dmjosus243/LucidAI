import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lucidai.db")

config = Config()