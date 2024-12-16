from multiprocessing import Event, Process
import subprocess
from threading import Lock

import NDIlib as ndi
from typing_extensions import Self

from main import logger, ndi_receiver_process, out_path, pano_process

from .schedulable import Schedulable


class FailedToStartRecordingException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class FailedToStopRecordingException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class RecordManager(Schedulable):
    __instance: Self | None = None
    __key = object()

    MAX_ATTEMPTS: int = 5

    @classmethod
    def get_instance(cls) -> Self:
        if cls.__instance is None:
            cls.__instance = cls(cls.__key)
        return cls.__instance

    def __init__(self, key):
        if key is not self.__key:
            raise ValueError("Cannot instantiate a new instance of this class, use get_instance instead")

        self._running = False
        self.__lock = Lock()

    def start(self, *args, **kwargs):
        with self.__lock:
            self._start(*args, **kwargs)

    def stop(self, *args, **kwargs):
        with self.__lock:
            self._stop(*args, **kwargs)

    @property
    def is_running(self) -> bool:
        with self.__lock:
            return self._running

    def _start(self, *args, **kwargs):
        if self._running:
            return

        self._running = True

        if not ndi.initialize():
            logger.error("Failed to initialize NDI.")
            raise FailedToStartRecordingException("Failed to initialize NDI.")

        ndi_find = ndi.find_create_v2()
        if ndi_find is None:
            logger.error("Failed to create NDI find instance.")
            raise FailedToStartRecordingException("Failed to create NDI find instance.")

        attempts: int = 0
        sources = []
        while len(sources) < 2 and attempts < self.MAX_ATTEMPTS:
            logger.info("Looking for sources ...")
            ndi.find_wait_for_sources(ndi_find, 5000)
            sources = ndi.find_get_current_sources(ndi_find)
            attempts += 1

        if len(sources) < 2:
            self._running = False
            raise FailedToStartRecordingException(f"Count not find enough sources. Sources found: {len(sources)}")

        ptz_urls = [source.url_address.split(':')[0] for source in sources]
        logger.info(ptz_urls)

        for url in ptz_urls:
            command = (
                rf'szCmd={{'
                rf'"SysCtrl":{{'
                rf'"PtzCtrl":{{'
                rf'"nChanel":0,"szPtzCmd":"preset_call","byValue":{1}'
                rf'}}'
                rf'}}'
                rf'}}'
            )

            subprocess.run(
                [
                    "curl",
                    f"http://{url}/ajaxcom",
                    "--data-raw",
                    command,
                ],
                check=False,
                capture_output=False,
                text=False,
            )

        start_event = Event()
        self.stop_event = Event()

        self.proc_pano = Process(
            target=pano_process,
            args=(
                "rtsp://root:oxittoor@192.168.33.103:554/media2/stream.sdp?profile=Profile200",
                ptz_urls,
                './rtdetrv2.onnx',
                self.stop_event,
                start_event,
            ),
        )
        self.proc_pano.start()

        start_event.wait()
        self.processes = []
        for idx, source in enumerate(sources):
            p = Process(
                target=ndi_receiver_process,
                args=((source.ndi_name, source.url_address), idx, out_path, self.stop_event),
            )
            self.processes.append(p)
            p.start()

        ndi.find_destroy(ndi_find)

    def _stop(self, *args, **kwargs):
        if not self._running:
            return

        self.stop_event.set()
        for process in self.processes:
            if process.is_alive():
                process.join()

        self.proc_pano.kill()

        self._running = False
