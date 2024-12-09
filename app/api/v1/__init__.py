from fastapi import APIRouter

from .camera import router as camera_router
from .schedule import router as schedule_router

router = APIRouter(prefix="/v1")
router.include_router(schedule_router)
router.include_router(camera_router)
