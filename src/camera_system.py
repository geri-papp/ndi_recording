import ndi
from ndi import CameraNDI
from rtsp import CameraRTSP
from utils import Camera, CameraOrientation


class CameraSystem:
    def __init__(self) -> None:

        ndi_sources, ndi_find = ndi.get_sources()

        self.cameras = {
            Camera.PTZ_MAIN: CameraNDI(src=ndi_sources[0], pos=Camera.PTZ_MAIN),
            Camera.PTZ_OTHER: CameraNDI(src=ndi_sources[1], pos=Camera.PTZ_OTHER),
            Camera.PANO: CameraRTSP(url=""),
        }

        ndi.find_destroy(ndi_find)

    def get_frame(self, camera: Camera) -> None:
        return self.cameras[camera].get_frame()

    def change_orientation(self, orientation: CameraOrientation) -> None:
        for camera in self.cameras.values():
            camera.orientation = orientation
