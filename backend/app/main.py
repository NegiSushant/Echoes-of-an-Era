import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.db.database import init_db
from app.api.memories import router as memories_router
from app.api.search import router as search_router
from app.api.ask import router as ask_router
from app.api.compare import router as compare_router

app = FastAPI(
    title="Echoes of an Era API",
    description="A living AI time capsule built from my grandfather's voice. AI interprets, never invents.",
    version="1.0.0"
)

# CORS configuration
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    print("[Backend] Initializing database schema and pgvector...")
    try:
        init_db()
        print("[Backend] Database ready.")
    except Exception as e:
        print(f"[Backend Warning] DB init deferred or encountered error: {e}")

# Register API Routers
app.include_router(memories_router)
app.include_router(search_router)
app.include_router(ask_router)
app.include_router(compare_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "project": "Echoes of an Era",
        "tagline": "A living AI time capsule built from my grandfather's voice",
        "principle": "AI interprets the memories. It does not create the memories."
    }

@app.get("/api/embeddings/info")
def get_embeddings_info():
    """Returns runtime model metadata for BAAI/bge-m3 embeddings."""
    from app.services.embeddings import embedding_service
    return embedding_service.get_model_info()

@app.get("/api/embeddings/test")
def test_embeddings():
    """Runs verification test on reference memory phrase."""
    from app.services.embeddings import embedding_service
    return embedding_service.test_embedding()

