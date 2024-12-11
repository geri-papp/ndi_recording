from typing import Annotated

from fastapi import APIRouter, Depends

from ...core.record_manager import RecordManager
from ...schemas.camera import CameraStatus
from ..dependencies import get_record_manager

router = APIRouter(prefix="/camera", tags=["Camera"])


@router.get("/status", response_model=CameraStatus)
def get_camera_status(
    record_manager: Annotated[
        RecordManager,
        Depends(get_record_manager),
    ],
):
    return CameraStatus(recording=record_manager.is_running)


@router.post("/start")
def start_camera(record_manager: Annotated[RecordManager, Depends(get_record_manager)]):
    record_manager.start()


@router.post("/stop")
def stop_camera(record_manager: Annotated[RecordManager, Depends(get_record_manager)]):
    record_manager.stop()


@router.post("/restart")
def restart_camera(record_manager: Annotated[RecordManager, Depends(get_record_manager)]):
    try:
        record_manager.stop()
    except ValueError:
        pass
    record_manager.start()
