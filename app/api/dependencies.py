from ..core.record_manager import RecordManager
from ..core.scheduler import Scheduler
from ..schemas.schedule import Schedule, SetSchedule


def get_schedule(set_schedule: SetSchedule):
    return Schedule(start_time=set_schedule.start_time, end_time=set_schedule.end_time)


def get_scheduler() -> Scheduler:
    return Scheduler.get_instance()


def get_record_manager() -> RecordManager:
    return RecordManager.get_instance()
