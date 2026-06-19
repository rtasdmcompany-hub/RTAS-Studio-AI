from fastapi import APIRouter

from app.api.routes import admin, ai, generate, health, upload

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(admin.router)
api_router.include_router(ai.router)
api_router.include_router(upload.router)
api_router.include_router(generate.router)
