from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router
import threading
import time
import logging

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Professional FastAPI Backend integrated with Next.js",
    version="1.0.0",
)

def prewarm_models():
    """
    Pre-warms the HuggingFace embeddings and Whisper models in a background thread at startup
    so the first request doesn't experience cold-start latency.
    """
    logger = logging.getLogger("app.main")
    logger.info("Initializing background model pre-warming...")
    
    # 1. Warm BGE Embedding model
    try:
        t0 = time.time()
        from app.services.embedder import TranscriptEmbedder
        TranscriptEmbedder.get_embeddings_model()
        logger.info(f"HuggingFace embedding model pre-warmed successfully in {time.time() - t0:.2f}s")
    except Exception as e:
        logger.error(f"Failed to pre-warm HuggingFace embedding model: {e}")
        
    # 2. Warm Whisper model
    try:
        t0 = time.time()
        from app.services.transcriber import Transcriber
        Transcriber.get_whisper_model()
        logger.info(f"Whisper model pre-warmed successfully in {time.time() - t0:.2f}s")
    except Exception as e:
        logger.error(f"Failed to pre-warm Whisper model: {e}")

@app.on_event("startup")
def startup_event():
    # Start pre-warming in a background daemon thread
    threading.Thread(target=prewarm_models, daemon=True).start()


# Set up CORS middleware to allow cross-origin requests from our Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include main api router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Also mount analysis router at root to support POST /analyze directly
from app.api.routes.analysis import router as analysis_router
app.include_router(analysis_router)

@app.get("/", tags=["health"])
def root():
    """
    Base endpoint for health checks and verification.
    """
    return {
        "status": "online",
        "message": f"Welcome to the {settings.PROJECT_NAME}!",
        "docs_url": "/docs"
    }

main = app

