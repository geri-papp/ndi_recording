from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from ...core.record_manager import RecordManager
from ...core.scheduler import Scheduler
from ...schemas.schedule import BadScheduleMessage, Schedule, ScheduleMessage
from ..dependencies import get_record_manager, get_schedule, get_scheduler

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.post("/add", response_model=ScheduleMessage)
def set_schedule(
    schedule: Annotated[Schedule, Depends(get_schedule)],
    scheduler: Annotated[Scheduler, Depends(get_scheduler)],
    record_manager: Annotated[RecordManager, Depends(get_record_manager)],
):
    try:
        id: int = scheduler.add_task(schedule=schedule, task=record_manager)
    except Exception as e:
        return BadScheduleMessage(message=str(e))

    return ScheduleMessage(
        success=True,
        id=id,
        message=f"Task scheduled with ID: {id}\nRemaining time until start: {schedule.start_time - datetime.now()}",
    )
