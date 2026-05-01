from fastapi import APIRouter

from app.api.routes import analyses, assets, evaluations, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(analyses.router, prefix="/analyses", tags=["analyses"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
