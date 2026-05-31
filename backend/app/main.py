from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Professional FastAPI Backend integrated with Next.js",
    version="1.0.0",
)

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

