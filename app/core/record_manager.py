from multiprocessing import Event, Process
from threading import Lock

import NDIlib as ndi
from typing_extensions import Self

from main import logger, ndi_receiver_process, out_path, pano_process

from .schedulable import Schedulable


class RecordManager(Schedulable):
    __instance: Self | None = None
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

    def _stop(self, *args, **kwargs):
        if not self._running:
            return

        self.stop_event.set()
        for process in self.processes:
            if process.is_alive():
                process.join()
            else:
                logger.warning(f"Process {process} not created.")

        self._running = False

    def _start(self, *args, **kwargs):
        if self._running:
            return

        self._running = True

        if not ndi.initialize():
            logger.error("Failed to initialize NDI.")
            raise ValueError("Failed to initialize NDI.")

        ndi_find = ndi.find_create_v2()
        if ndi_find is None:
            logger.error("Failed to create NDI find instance.")
            raise ValueError("Failed to create NDI find instance.")

        sources = []
        while len(sources) < 2:
            logger.info("Looking for sources ...")
            ndi.find_wait_for_sources(ndi_find, 5000)
            sources = ndi.find_get_current_sources(ndi_find)
            # print(sources[0].ndi_name)

        # for source in sources:
        #     print(source.ndi_name, source.url_address)

        ptz_urls = [source.url_address.split(':')[0] for source in sources]

        start_event = Event()
        stop_event = Event()

        proc_pano = Process(
            target=pano_process,
            args=(
                "rtsp://root:oxittoor@192.168.33.103:554/media2/stream.sdp?profile=Profile200",
                ptz_urls,
                './rtdetrv2.onnx',
                stop_event,
                start_event,
            ),
        )
        proc_pano.start()

        start_event.wait()
        processes = []
        for idx, source in enumerate(sources):
            p = Process(
                target=ndi_receiver_process,
                args=((source.ndi_name, source.url_address), idx, out_path, self.stop_event),
            )
            self.processes.append(p)
            p.start()

        ndi.find_destroy(ndi_find)
