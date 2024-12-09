from pydantic import BaseModel, Field, root_validator
from datetime import datetime, timedelta
from typing import Annotated


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

    @root_validator(pre=True)
    def validate_schedule(cls, values):
        start_time = values.get("start_time")
        end_time = values.get("end_time")
        duration = values.get("duration")

        if end_time is not None and duration is not None:
            raise ValueError("Either end_time or duration should be provided, not both.")
        if end_time is None and duration is None:
            raise ValueError("Either end_time or duration should be provided.")

        if end_time is not None:
            values["duration"] = end_time - start_time
        if duration is not None:
            values["end_time"] = start_time + duration

        return values

    def to_schedule(self) -> Schedule:
        if self.end_time is not None and self.duration is not None:
            raise ValueError("Either end_time or duration should be provided, not both.")

        if self.end_time is not None:
            self.duration = self.end_time - self.start_time

        if self.duration is not None:
            self.end_time = self.start_time + self.duration

        assert self.end_time is not None
        return Schedule(start_time=self.start_time, end_time=self.end_time)
