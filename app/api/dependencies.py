from ..core.record_manager import RecordManager
from ..core.scheduler import Scheduler
from ..schemas.schedule import Schedule, SetSchedule


async def get_schedule(set_schedule: SetSchedule):
    assert set_schedule.end_time is not None, 'end_time is required'

    return Schedule(start_time=set_schedule.start_time, end_time=set_schedule.end_time)


async def get_scheduler() -> Scheduler:
    return Scheduler.get_instance()


async def get_record_manager() -> RecordManager:
    return RecordManager.get_instance()
