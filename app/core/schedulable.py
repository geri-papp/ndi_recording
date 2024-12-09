import abc


@abc.abstractmethod
class Schedulable:
    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass
