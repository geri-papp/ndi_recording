from pydantic import BaseModel, Field
from typing import Annotated


class CameraStatus(BaseModel):
    recording: Annotated[
        bool,
        Field(
            description="Recording status of the camera",
            examples=[True, False],
        ),
    ]
