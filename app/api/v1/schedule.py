from datetime import datetime
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
    if schedule.start_time < datetime.now():
        return BadScheduleMessage(message="Start time cannot be in the past")

    try:
        id: int = scheduler.add_task(schedule=schedule, task=record_manager)
    except Exception as e:
        return BadScheduleMessage(message=str(e))

    return ScheduleMessage(
        success=True,
        id=id,
        message=f"Task scheduled with ID: {id}\nRemaining time until start: {schedule.start_time - datetime.now()}",
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
