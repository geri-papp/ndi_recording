from fastapi import APIRouter

from .camera import router as camera_router

router = APIRouter(prefix="/v1")
router.include_router(camera_router)
