from typing import Annotated

from pydantic import BaseModel, Field


class CameraStatus(BaseModel):
    recording: Annotated[
        bool,
        Field(
            description="Recording status of the camera",
            examples=[True, False],
        ),
    ]
