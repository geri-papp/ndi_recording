from typing import Annotated

from pydantic import BaseModel, Field

from .schedule import Schedule


class ScheduledTaskSchema(BaseModel):
    id: Annotated[
        int,
        Field(
            description="ID of the scheduled task",
            examples=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        ),
    ]
    schedule: Annotated[
        Schedule,
        Field(
            description="Schedule of the task",
        ),
    ]
    is_running: Annotated[
        bool,
        Field(
            description="Status of the task",
            examples=[True, False],
        ),
    ]
