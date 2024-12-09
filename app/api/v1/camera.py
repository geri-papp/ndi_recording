from typing import Annotated

from fastapi import APIRouter, Depends

from ...core.record_manager import RecordManager
from ...schemas.camera import CameraStatus
from ..dependencies import get_record_manager

router = APIRouter(prefix="/camera", tags=["Camera"])


@router.get("/status", response_model=CameraStatus)
async def get_camera_status():
    raise NotImplementedError("Getting camera status is not implemented yet.")


@router.post("/start")
async def start_camera(record_manager: Annotated[RecordManager, Depends(get_record_manager)]):
    record_manager.start()


@router.post("/stop")
async def stop_camera(record_manager: Annotated[RecordManager, Depends(get_record_manager)]):
    record_manager.stop()


@router.post("/restart")
async def restart_camera(record_manager: Annotated[RecordManager, Depends(get_record_manager)]):
    try:
        record_manager.stop()
    except ValueError:
        pass
    record_manager.start()
