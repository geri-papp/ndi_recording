from datetime import datetime
from threading import Event, Thread

from typing_extensions import Self

from ..schemas.schedule import Schedule
from .schedulable import Schedulable


class ScheduledTask:
    def __init__(self, id: int, schedule: Schedule, task: Schedulable):
        self.id = id
        self.schedule = schedule
        self.task = task
        self._running = False

    def __str__(self):
        return f'ScheduledTask(id={self.id}, schedule={self.schedule}, task={self.task})'

    def __repr__(self):
        return str(self)

    def start(self):
        if self._running:
            return

        self._running = True
        self.task.start()

    def stop(self):
        if not self._running:
            return

        self.task.stop()
        self._running = False

    def is_due_to_start(self):
        return self.schedule.start_time <= datetime.now() and not self._running

    def is_due_to_stop(self):
        return self.schedule.end_time <= datetime.now() and self._running


class Scheduler:
    __instance: Self | None = None
    __key = object()

    @classmethod
    def get_instance(cls) -> Self:
        if cls.__instance is None:
            cls.__instance = cls(cls.__key)
            cls.__instance.start()

        return cls.__instance

    def __init__(self, key, check_interval: int = 1, end_event: Event | None = None):
        if key is not self.__key:
            raise ValueError("Cannot instantiate a new instance of this class, use get_instance instead")

        self.__tasks: dict[int, ScheduledTask] = {}
        self.__check_interval = check_interval
        self.__end_event = end_event or Event()

        self.__thread: Thread | None = None

    def __del__(self):
        self.stop()

    def add_task(self, schedule: Schedule, task: Schedulable, id: int | None = None) -> int:
        if id is None:
            id = max(self.__tasks.keys(), default=-1) + 1

        if id in self.__tasks:
            raise ValueError(f'Task with id {id} already exists')

        self.__tasks[id] = ScheduledTask(id, schedule, task)

        return id

    def remove_task(self, id: int, stop_task: bool = True):
        if id not in self.__tasks:
            raise ValueError(f'Task with id {id} does not exist')

        if stop_task:
            self.__tasks[id].stop()

        del self.__tasks[id]

    def get_task(self, id: int) -> ScheduledTask:
        if id not in self.__tasks:
            raise ValueError(f'Task with id {id} does not exist')

        return self.__tasks[id]

    def get_tasks(self) -> list[ScheduledTask]:
        return list(self.__tasks.values())

    def start(self):
        self.__end_event.clear()
        self.__thread = Thread(target=self.__run, daemon=True)
        self.__thread.start()

    def stop(self):
        self.__end_event.set()
        if self.__thread is not None and self.__thread.is_alive():
            self.__thread.join()

    def __run(self):
        while not self.__end_event.is_set():
            for task in self.__tasks.values():
                if task.is_due_to_start():
                    task.start()
                elif task.is_due_to_stop():
                    task.stop()

            self.__end_event.wait(self.__check_interval)

        for task in self.__tasks.values():
            task.stop()
