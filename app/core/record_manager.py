from typing_extensions import Self

from .schedulable import Schedulable


class RecordManager(Schedulable):
    __key = object()

    @classmethod
    def get_instance(cls) -> Self:
        if cls.__instance is None:
            cls.__instance = cls(cls.__key)
        return cls.__instance

    def __init__(self, key):
        if key is not self.__key:
            raise ValueError("Cannot instantiate a new instance of this class, use get_instance instead")

    def start(self, *args, **kwargs):
        raise NotImplementedError("RecordManager.start() is not implemented")

    def stop(self, *args, **kwargs):
        raise NotImplementedError("RecordManager.stop() is not implemented")
