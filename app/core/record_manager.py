from multiprocessing import Event, Process

from typing_extensions import Self

from src.camera_system import CameraSystem
from src.logger import LOG_DIR, logger
from src.utils import Camera

from ...main import ndi_process, rtsp_process
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

        self._running = False

    def start(self, *args, **kwargs):
        if self._running:
            raise ValueError("RecordManager is already running")

        self._running = True

        self.camera_system = CameraSystem()
        self.processes: list[Process] = []
        self.stop_event = Event()
        for camera in self.camera_system.cameras:
            if camera != Camera.PANO:
                p = Process(target=ndi_process, args=(self.camera_system, camera, LOG_DIR, self.stop_event))
            else:
                p = Process(
                    target=rtsp_process,
                    args=(self.camera_system, camera, self.stop_event, (1920, 1080), './rtdetrv2.onnx'),
                )
            self.processes.append(p)
            p.start()

    def stop(self, *args, **kwargs):
        if not self._running:
            raise ValueError("RecordManager is not running")

        self.stop_event.set()
        for process in self.processes:
            if process.is_alive():
                process.join()
            else:
                logger.warning(f"Process {process} not created.")

        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running
