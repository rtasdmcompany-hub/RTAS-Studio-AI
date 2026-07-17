from fastapi import APIRouter

from app.api.routes import (
    admin,
    ai,
    audio,
    audio_engine,
    camera_motion,
    generate,
    health,
    image_to_video,
    intelligence,
    jobs,
    lip_sync,
    motion_intelligence,
    multi_ai,
    multi_gpu,
    physics,
    scene_render,
    talking_avatar,
    text_to_video,
    upload,
    video_engine,
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
api_router.include_router(motion_intelligence.router)
api_router.include_router(camera_motion.router)
api_router.include_router(physics.router)
api_router.include_router(scene_render.router)
api_router.include_router(multi_gpu.router)
api_router.include_router(video_engine.router)
api_router.include_router(audio_engine.router)
api_router.include_router(audio.router)
