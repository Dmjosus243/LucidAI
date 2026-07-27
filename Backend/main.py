from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import config
from api.routes import upload, analysis, reports

# Stockage mémoire (pour MVP)
temp_storage = {}

app = FastAPI(title="LucidAI API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "healthy", "env": config.ENVIRONMENT}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)