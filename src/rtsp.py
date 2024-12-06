import cv2

from src.logger import logger


class CameraRTSP:
    def __init__(self, url: str) -> None:

        self.video_cap = cv2.VideoCapture(url)
        if not self.video_cap.isOpened():
            logger.warning("Cannot open RTSP stream.")

    def get_frame(self):
        ret, frame = self.video_cap.read()

        return frame[420:1150, 1190:3390] if ret else None

    def stop(self) -> None:
        self.video_cap.release()
