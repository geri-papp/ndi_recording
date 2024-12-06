import subprocess
from typing import List

import NDIlib as ndi
import numpy as np

from src.logger import logger
from src.utils import Camera, CameraOrientation


class CameraNDI:
    def __init__(self, src, camera: Camera, fps: int = 50) -> None:
        self.fps = fps

        self.__camera = camera
        self.__ip_addrs = src.url_address.split(':')[0]

        self.__orientation = None
        self.orientation = CameraOrientation.CENTER

        self.receiver = self.__create_receiver(src)

    def __create_receiver(self, src):

        ndi_recv_create = ndi.RecvCreateV3()
        ndi_recv_create.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
        receiver = ndi.recv_create_v3(ndi_recv_create)
        if receiver is None:
            raise RuntimeError("Failed to create NDI receiver")
        ndi.recv_connect(receiver, src)

        return receiver

    def get_frame(self):

        t, v, _, _ = ndi.recv_capture_v3(self.receiver, 1000)
        frame = None
        if t == ndi.FRAME_TYPE_VIDEO:
            frame = np.copy(v.data[:, :, :3])
            ndi.recv_free_video_v2(self.receiver, v)

        return frame, t

    @property
    def camera(self):
        return self.__camera

    @property
    def orientation(self):
        return self.__orientation

    @orientation.setter
    def orientation(self, ori: CameraOrientation):
        if self.orientation != ori:
            self.__orientation = ori

            command = (
                rf'szCmd={{'
                rf'"SysCtrl":{{'
                rf'"PtzCtrl":{{'
                rf'"nChanel":0,"szPtzCmd":"preset_call","byValue":{self.orientation.value}'
                rf'}}'
                rf'}}'
                rf'}}'
            )

            subprocess.run(
                [
                    "curl",
                    f"http://{self.__ip_addrs}/ajaxcom",
                    "--data-raw",
                    command,
                ],
                check=False,
                capture_output=False,
                text=False,
            )


def get_sources(wait: int = 5000) -> List:

    if not ndi.initialize():
        logger.error("Failed to initialize NDI.")
        return 1

    ndi_find = ndi.find_create_v2()
    if ndi_find is None:
        logger.error("Failed to create NDI find instance.")
        return 1

    sources = []
    while len(sources) < 2:
        logger.info("Looking for sources ...")
        ndi.find_wait_for_sources(ndi_find, wait)
        sources = ndi.find_get_current_sources(ndi_find)

    return sources, ndi_find


def find_destroy(ndi_find) -> None:
    ndi.find_destroy(ndi_find)
