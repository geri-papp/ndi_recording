from typing import Annotated

from pydantic import BaseModel, Field


class DetailSchema(BaseModel):
    error: Annotated[
        str,
        Field(
            description="The error that occured",
            examples=["Camera failed to start", "Camera failed to stop"]
        ),
    ]
    reason: Annotated[
        str | None,
        Field(
            description="The reason for the error",
            examples=[
                "Failed to initialize NDI.", "Count not find enough sources."
            ]
        ),
    ]


class CameraExceptionSchema(BaseModel):
    status_code: Annotated[
        int,
        Field(
            description="Status code of the exceptiob",
            examples=[500],
        ),
    ]
    detail: Annotated[
        DetailSchema,
        Field(
            description="The details of the error",
        ),
    ]
