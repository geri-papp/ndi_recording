from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import HTTPException, status

from ...schemas.schedule import ScheduledTaskIsInThePastDetailSchema, DuplicateScheduleDetailSchema, ScheduleNotFoundDetailSchema


class CustomException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str | None = None,
    ):
        if detail is None:
            detail = HTTPStatus(status_code).description
        super().__init__(status_code=status_code, detail=detail)


class FailedToStartCameraException(HTTPException):
    def __init__(self, extra_detail: str | None = None):
        detail = {
            "error": "Camera failed to start",
            "reason": None
        }
        if extra_detail is not None:
            detail.update({"reason": extra_detail})

        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class FailedToStopCameraException(HTTPException):
    def __init__(self, extra_detail: str | None = None):
        detail = {
            "error": "Camera failed to stop",
            "reason": None
        }
        if extra_detail is not None:
            detail.update({"reason": extra_detail})

        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class ScheduledTaskIsInThePastException(HTTPException):
    def __init__(self, scheduled_time: datetime):
        detail = ScheduledTaskIsInThePastDetailSchema(
            error="Start time cannot be in the past",
            scheduled_time=scheduled_time,
            current_time=datetime.now(timezone.utc).replace(tzinfo=None)
        )

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail.model_dump(),
        )


class DuplicateScheduleIdException(HTTPException):
    def __init__(self, id: int):
        detail = DuplicateScheduleDetailSchema(
            error="Scheduled task with the same id already exists",
            id=id,
        )

        super().__init__(
            status_code=status.HTTP_409_CONFICT,
            detail=detail.model_dump(),
        )


class ScheduleNotFoundException(HTTPException):
    def __init__(self, id: int):
        detail = ScheduleNotFoundDetailSchema(
            error="Schedule with the given id not found",
            id=id,
        )

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail.model_dump(),
        )
