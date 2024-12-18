import abc


class Schedulable(abc.ABC):
    @abc.abstractmethod
    def start(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def stop(self, *args, **kwargs):
        pass

    @property
    @abc.abstractmethod
    def is_running(self) -> bool:
        pass
