from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from ...core.record_manager import RecordManager
from ...core.scheduler import Scheduler
from ...schemas.schedule import BadScheduleMessage, Schedule, ScheduleMessage
from ...schemas.scheduled_task import ScheduledTaskSchema
from ..dependencies import get_record_manager, get_schedule, get_scheduler

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.get(
    "/",
    response_model=list[ScheduledTaskSchema],
    status_code=status.HTTP_200_OK,
)
def get_tasks(scheduler: Annotated[Scheduler, Depends(get_scheduler)]):
    return [
        ScheduledTaskSchema(
            id=task.id,
            schedule=task.schedule,
            is_running=task._running,
        )
        for task in scheduler.get_tasks()
    ]


@router.get(
    "/{id}",
    response_model=ScheduledTaskSchema,
    status_code=status.HTTP_200_OK,
)
def get_task(
    *,
    id: Annotated[int, Path(description="ID of the task to get")],
    scheduler: Annotated[Scheduler, Depends(get_scheduler)],
):
    task = scheduler.get_task(id)
    return ScheduledTaskSchema(
        id=task.id,
        schedule=task.schedule,
        is_running=task._running,
    )


@router.post(
    "/",
    response_model=ScheduleMessage,
    status_code=status.HTTP_201_CREATED,
)
def set_schedule(
    schedule: Annotated[Schedule, Depends(get_schedule)],
    scheduler: Annotated[Scheduler, Depends(get_scheduler)],
    record_manager: Annotated[RecordManager, Depends(get_record_manager)],
):
    if schedule.start_time < datetime.now(timezone.utc).replace(tzinfo=None):
        return BadScheduleMessage(message="Start time cannot be in the past")

    try:
        id: int = scheduler.add_task(schedule=schedule, task=record_manager)
    except Exception as e:
        return BadScheduleMessage(message=str(e))

    remaining_time: timedelta = schedule.start_time - datetime.now(timezone.utc).replace(tzinfo=None)
    hours, remainder = divmod(remaining_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    display_time: str  # In $HH:$MM:$SS format
    if remaining_time.days > 0:
        day_str: str = "days" if remaining_time.days > 1 else "day"
        display_time = f"{remaining_time.days} {day_str}, {hours:02}:{minutes:02}:{seconds:02}"
    else:
        display_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    return ScheduleMessage(
        success=True,
        id=id,
        message=f"Remaining time: {display_time}",
    )


@router.delete(
    "/{id}",
    response_model=ScheduleMessage,
    status_code=status.HTTP_200_OK,
)
def remove_schedule(
    *,
    id: Annotated[int, Path(description="ID of the task to remove")],
    stop_task: Annotated[
        bool,
        Query(
            description="Stop the task if it is running",
        ),
    ] = True,
    scheduler: Annotated[Scheduler, Depends(get_scheduler)],
):
    try:
        scheduler.remove_task(id, stop_task=stop_task)
    except Exception as e:
        return BadScheduleMessage(message=str(e))
    return ScheduleMessage(success=True, id=id, message="Task removed")
