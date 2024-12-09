from datetime import datetime, timedelta
from typing import Annotated

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self


class ScheduleMessage(BaseModel):
    success: Annotated[
        bool,
        Field(
            description="Success status of the operation",
            examples=[True, False],
        ),
    ]
    id: Annotated[
        int | None,
        Field(
            description="ID of the schedule",
            examples=[0, 1, 2, None],
        ),
    ]
    message: Annotated[
        str,
        Field(
            description="Message to be displayed",
            examples=["Hello, World!"],
        ),
    ]


class Schedule(BaseModel):
    start_time: Annotated[
        datetime,
        Field(
            description="Start time of the schedule",
            examples=["2021-08-01T12:30:00"],
        ),
    ]
    end_time: Annotated[
        datetime,
        Field(
            description="End time of the schedule",
            examples=["2021-08-01T13:30:00"],
        ),
    ]


class SetSchedule(BaseModel):
    start_time: Annotated[
        datetime,
        Field(
            description="Start time of the schedule",
            examples=["2021-08-01T12:30:00"],
        ),
    ]
    end_time: Annotated[
        datetime | None,
        Field(
            description="End time of the schedule",
            examples=["2021-08-01T13:30:00"],
        ),
    ]
    duration: Annotated[
        timedelta | None,
        Field(
            description="Duration of the schedule",
            examples=["1:00:00"],
        ),
    ]

    @model_validator(mode="before")
    def validate_schedule(self) -> Self:
        if self.end_time is not None and self.duration is not None:
            raise ValueError("Either end_time or duration should be provided, not both.")
        if self.end_time is None and self.duration is None:
            raise ValueError("Either end_time or duration should be provided.")

        if self.end_time is not None:
            self.duration = self.end_time - self.start_time
        elif self.duration is not None:
            self.end_time = self.start_time + self.duration

        assert self.end_time is not None
        if self.end_time < self.start_time:
            raise ValueError("end_time should be greater than start_time.")

        return self

    def to_schedule(self) -> Schedule:
        if self.end_time is not None and self.duration is not None:
            raise ValueError("Either end_time or duration should be provided, not both.")

        if self.end_time is not None:
            self.duration = self.end_time - self.start_time

        if self.duration is not None:
            self.end_time = self.start_time + self.duration

        assert self.end_time is not None
        return Schedule(start_time=self.start_time, end_time=self.end_time)
