import abc


@abc.abstractmethod
class Schedulable:
    @abc.abstractmethod
    def start(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def stop(self, *args, **kwargs):
        pass
