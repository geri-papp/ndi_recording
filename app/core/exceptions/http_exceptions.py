from http import HTTPStatus

from fastapi import HTTPException, status


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
