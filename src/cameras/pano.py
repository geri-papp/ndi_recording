import cv2
from typing import Tuple
import numpy as np
from src.logger import logger


class CameraPano:
    def __init__(self, url: str, fps: int, roi: Tuple[int] = None) -> None:

        self.fps = fps
        self.has_roi = roi is not None

        self.video_cap = cv2.VideoCapture(url)
        if not self.video_cap.isOpened():
            logger.warning("Cannot open RTSP stream.")

        if self.has_roi:
            self.slice_y = slice(roi[0], roi[2]) if roi is not None else None
            self.slice_x = slice(roi[1], roi[3]) if roi else None
            self.frame_size = np.array([self.slice_y.stop - self.slice_y.start, self.slice_x.stop - self.slice_x.start])
        else:
            ret, frame = self.video_cap.read()
            self.frame_size = np.array([frame.shape[0], frame.shape[1]])

    def get_frame(self):
        ret, frame = self.video_cap.read()

        return frame[420:1150, 1190:3390] if ret else None

    def stop(self) -> None:
        self.video_cap.release()
