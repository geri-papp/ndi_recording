from enum import Enum


class Camera(Enum):
    PTZ_MAIN = 0
    PTZ_OTHER = 1
    PANO = 2


class CameraOrientation(Enum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2
