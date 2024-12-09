from typing import Annotated
from fastapi import APIRouter, Depends


from ...schemas.camera import CameraStatus
from ...schemas.schedule import Schedule
from ..dependencies import get_schedule

router = APIRouter(prefix="/camera", tags=["Camera"])


@router.get("/status", response_model=CameraStatus)
async def get_camera_status():
    raise NotImplementedError("Getting camera status is not implemented yet.")


@router.post("/start")
async def start_camera(schedule: Annotated[Schedule, Depends(get_schedule)]):
    raise NotImplementedError("Starting camera is not implemented yet.")


@router.post("/stop")
async def stop_camera():
    raise NotImplementedError("Stopping camera is not implemented yet.")


@router.post("/restart")
async def restart_camera():
    raise NotImplementedError("Restarting camera is not implemented yet.")
