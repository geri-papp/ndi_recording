from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from ...core.exceptions.http_exceptions import FailedToStartCameraException, FailedToStopCameraException
from ...core.record_manager import FailedToStartRecordingException, FailedToStopRecordingException, RecordManager
from ...core.scheduler import Scheduler
from ...schemas.camera import CameraStatus
from ...schemas.exceptions import CameraExceptionSchema
from ..dependencies import get_record_manager, get_scheduler

router = APIRouter(prefix="/camera", tags=["Camera"])

responses: dict[int, dict[str, Any]] = {
    202: {"model": CameraStatus},
    500: {
        "description": "Error during camera start/stop",
        "model": CameraExceptionSchema,
    },
}


@router.get("/status", response_model=CameraStatus)
def get_camera_status(
    record_manager: Annotated[
        RecordManager,
        Depends(get_record_manager),
    ],
):
    return CameraStatus(recording=record_manager.is_running)


@router.post("/start", status_code=status.HTTP_200_OK, response_model=CameraStatus, responses={**responses})
def start_camera(record_manager: Annotated[RecordManager, Depends(get_record_manager)]):
    status = CameraStatus(recording=True)

    if record_manager.is_running:
        return JSONResponse(status_code=202, content=status.model_dump())

    try:
        record_manager.start(datetime.now())
    except FailedToStartRecordingException as e:
        raise FailedToStartCameraException(e.message)

    return status


@router.post("/stop", status_code=status.HTTP_200_OK, response_model=CameraStatus, responses={**responses})
def stop_camera(
    record_manager: Annotated[RecordManager, Depends(get_record_manager)],
    scheduler: Annotated[Scheduler, Depends(get_scheduler)],
):
    status = CameraStatus(recording=False)

    if not record_manager.is_running:
        return JSONResponse(status_code=202, content=status.model_dump())

    try:
        success = scheduler.stop_running_task()
        if not success:
            record_manager.stop()
    except FailedToStopRecordingException as e:
        raise FailedToStopCameraException(e.message)

    return status


@router.post("/restart", status_code=status.HTTP_200_OK, response_model=CameraStatus, responses={**responses})
def restart_camera(record_manager: Annotated[RecordManager, Depends(get_record_manager)]):
    try:
        record_manager.stop()
        record_manager.start(datetime.now())
    except FailedToStopRecordingException as e:
        raise FailedToStopCameraException(e.message)
    except FailedToStartRecordingException as e:
        raise FailedToStartCameraException(e.message)

    return CameraStatus(recording=True)
