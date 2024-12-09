from datetime import datetime, timedelta
from typing import Annotated

from pydantic import BaseModel, Field, model_validator


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


class BadScheduleMessage(ScheduleMessage):
    def __init__(self, message: str) -> None:
        super().__init__(success=False, id=None, message=message)


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
    @classmethod
    def validate_schedule(cls, data: dict) -> dict:
        start_time_str: str = data["start_time"]
        end_time_str: str | None = data.get("end_time")
        duration_str: str | None = data.get("duration")
        start_time: datetime = datetime.fromisoformat(start_time_str)
        end_time: datetime | None = datetime.fromisoformat(end_time_str) if end_time_str else None
        duration_datetime: datetime | None = datetime.fromisoformat(duration_str) if duration_str else None
        duration: timedelta | None = (
            duration_datetime - datetime.fromisoformat("1900-01-01T00:00:00") if duration_datetime else None
        )

        if end_time is not None and duration is not None:
            raise ValueError("Either end_time or duration should be provided, not both.")
        if end_time is None and duration is None:
            raise ValueError("Either end_time or duration should be provided.")

        if end_time is not None:
            duration = end_time - start_time
        if duration is not None:
            end_time = start_time + duration

        assert end_time is not None
        if end_time < start_time:
            raise ValueError("end_time should be greater than start_time.")

        return {"start_time": start_time, "end_time": end_time, "duration": duration}

    def to_schedule(self) -> Schedule:
        if self.end_time is not None and self.duration is not None:
            raise ValueError("Either end_time or duration should be provided, not both.")

        if self.end_time is not None:
            self.duration = self.end_time - self.start_time

        if self.duration is not None:
            self.end_time = self.start_time + self.duration

        assert self.end_time is not None
        return Schedule(start_time=self.start_time, end_time=self.end_time)
