from fastapi import APIRouter

from app.api.routes import (
    admin,
    ai,
    generate,
    health,
    image_to_video,
    intelligence,
    jobs,
    lip_sync,
    multi_ai,
    talking_avatar,
    text_to_video,
    upload,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(admin.router)
api_router.include_router(ai.router)
api_router.include_router(upload.router)
api_router.include_router(generate.router)
api_router.include_router(jobs.router)
api_router.include_router(intelligence.router)
api_router.include_router(multi_ai.router)
api_router.include_router(text_to_video.router)
api_router.include_router(image_to_video.router)
api_router.include_router(talking_avatar.router)
api_router.include_router(lip_sync.router)
