from fastapi import APIRouter
from app.api.routes import items, analysis

api_router = APIRouter()

# Register routes
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
