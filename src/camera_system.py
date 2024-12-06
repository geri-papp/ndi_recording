import src.ndi as ndi
from src.ndi import CameraNDI
from src.rtsp import CameraRTSP
from src.utils import Camera, CameraOrientation


class CameraSystem:
    def __init__(self) -> None:

        ndi_sources, ndi_find = ndi.get_sources()

        self.orientation = CameraOrientation.CENTER
        self.cameras = {
            Camera.PTZ_MAIN: CameraNDI(src=ndi_sources[1], camera=Camera.PTZ_MAIN),
            Camera.PTZ_OTHER: CameraNDI(src=ndi_sources[0], camera=Camera.PTZ_OTHER),
            Camera.PANO: CameraRTSP(
                url="/media/geri/88438b12-8823-446e-b364-546efb5da056/datasets/wp_old/videos/tmp.mp4"
            ),
        }

        ndi.find_destroy(ndi_find)

    def get_frame(self, camera: Camera) -> None:
        return self.cameras[camera].get_frame()

    def change_orientation(self, orientation: CameraOrientation) -> None:
        if self.orientation != orientation:
            self.orientation = orientation

            for camera in self.cameras.values():
                if camera != Camera.PANO:
                    camera.orientation = orientation
