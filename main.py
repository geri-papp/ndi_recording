import os
import NDIlib as ndi
import subprocess
import logging
import numpy as np
from multiprocessing import Process, Event
import argparse
from typing import Tuple
from tqdm import tqdm
import onnxruntime
import time
import cv2
from typing import List
from collections import deque, Counter

import time
from datetime import datetime, timedelta

out_path = f"{os.getcwd()}/output/{datetime.now().strftime('%Y%m%d_%H%M')}"
os.makedirs(out_path, exist_ok=True)


def create_logger():
    l = logging.getLogger("ndi_logger")
    l.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    file_handler = logging.FileHandler(f"{out_path}/run.log", mode="w")
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="{asctime} - [{levelname}]: {message}",
        style="{",
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    l.addHandler(console_handler)
    l.addHandler(file_handler)

    return l


logger = create_logger()


def process_buckets(boxes, labels, scores, bucket_width):
    buckets = {0: 0, 1: 0, 2: 0}
    bboxes_player = boxes[(labels == 2) & (scores > 0.5)]
    centers_x = (bboxes_player[:, 0] + bboxes_player[:, 2]) / 2

    for center_x in centers_x:
        bucket_idx = center_x // bucket_width
        buckets[bucket_idx] += 1

    return max(buckets, key=lambda k: buckets[k])


def update_frequency(window, freq_counter, bucket, max_window_size=50):
    """
    Update the sliding window and frequency counter to track the most frequent bucket.
    """
    window.append(bucket)
    freq_counter[bucket] += 1

    if len(window) > max_window_size:
        oldest = window.popleft()
        freq_counter[oldest] -= 1
        if freq_counter[oldest] == 0:
            del freq_counter[oldest]

    # Return the most common bucket
    return freq_counter.most_common(1)[0][0]


def pano_process(
    url: str,
    ptz_urls: List,
    onnx_file: str,
    stop_event: Event,
    start_event: Event,
    fps: int = 15,
):
    """ """

    frame_size = np.array([730, 2200])
    sleep_time = 1 / fps
    bucket_width = frame_size[1] // 3

    onnx_session = onnxruntime.InferenceSession(onnx_file, providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
    logger.info(f"ONNX Model Device: {onnxruntime.get_device()}")

    window = deque()
    freq_counter = Counter()

    video_capture = cv2.VideoCapture(url)

    start_event.set()
    try:
        while not stop_event.is_set():
            ret, frame = video_capture.read()

            if not ret:
                logger.warning(f"No panorama frame captured.")
                continue
            frame = frame[420:1150, 1190:3390]
            img = cv2.resize(frame, (640, 640), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
            img = np.expand_dims(np.transpose(img, (2, 0, 1)), axis=0)

            labels, boxes, scores = onnx_session.run(
                output_names=None,
                input_feed={
                    'images': img,
                    "orig_target_sizes": frame_size[::-1],
                },
            )

            most_populated_bucket = process_buckets(boxes, labels, scores, bucket_width)
            mode = update_frequency(window, freq_counter, most_populated_bucket)

            for url in ptz_urls:
                command = (
                    rf'szCmd={{'
                    rf'"SysCtrl":{{'
                    rf'"PtzCtrl":{{'
                    rf'"nChanel":0,"szPtzCmd":"preset_call","byValue":{mode}'
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

            time.sleep(sleep_time)

    except KeyboardInterrupt:
        video_capture.release()

    logger.info(f"RTSP Receiver Process stopped.")


class NDIReceiver:
    def __init__(self, src, idx: int, path, codec="h264_nvenc", fps: int = 50) -> None:
        self.idx = idx
        self.codec = codec
        self.fps = fps
        self.path = path

        self.receiver = self.create_receiver(src)
        self.ffmpeg_process = self.start_ffmpeg_process()

    def create_receiver(self, src):

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
            # logger.info("Frame received")
            frame = np.copy(v.data[:, :, :3])
            ndi.recv_free_video_v2(self.receiver, v)
            # cv2.imwrite('output/asd.png', frame)
            # print(frame.shape)

        return frame, t

    def start_ffmpeg_process(self):
        return subprocess.Popen(
            [
                "ffmpeg",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "bgr24",
                "-s",
                "1920x1080",
                "-r",
                str(self.fps),
                "-hwaccel",
                "cuda",
                "-hwaccel_output_format",
                "cuda",
                "-i",
                "pipe:",
                "-c:v",
                self.codec,
                "-pix_fmt",
                "yuv420p",
                "-b:v",
                "35000k",
                "-preset",
                "fast",
                "-profile:v",
                "high",
                os.path.join(self.path, f"cam{self.idx}.mp4"),
            ],
            stdin=subprocess.PIPE,
        )

    def stop(self) -> None:
        if self.ffmpeg_process.stdin:
            try:
                self.ffmpeg_process.stdin.flush()
                self.ffmpeg_process.stdin.close()
            except BrokenPipeError as e:
                logger.error(f"Broken pipe error while closing stdin: {e}")

        self.ffmpeg_process.wait()


def ndi_receiver_process(src, idx: int, path, stop_event: Event, codec: str = "h264_nvenc", fps: int = 50):

    receiver = NDIReceiver(src, idx, path, codec, fps)

    logger.info(f"NDI Receiver {idx} created.")

    try:
        while not stop_event.is_set():
            frame, t = receiver.get_frame()
            if frame is not None:
                try:
                    receiver.ffmpeg_process.stdin.write(frame.tobytes())
                    receiver.ffmpeg_process.stdin.flush()
                except BrokenPipeError as e:
                    logger.error(f"Broken pipe error while writing frame: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error in NDI Receiver Process {idx}: {e}")
                    break
            else:
                logger.warning(f"No video frame captured. Frame type: {t}")
    except KeyboardInterrupt:
        receiver.stop()

    logger.info(f"NDI Receiver Process {receiver.idx} stopped.")


def schedule(start_time: datetime, end_time: datetime) -> None:

    sleep_time = int((start_time - datetime.now()).total_seconds())
    if sleep_time <= 0:
        return

    hours, remainder = divmod(sleep_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    logger.info(
        f"Waiting for {hours:02d}:{minutes:02d}:{seconds:02d} (hh:mm:ss) until {end_time.strftime('%Y.%m.%d %H:%M:%S')}."
    )

    with tqdm(total=sleep_time, bar_format="{l_bar}{bar} [Elapsed: {elapsed}, Remaining: {remaining}]") as progress:
        for _ in range(int(sleep_time)):
            time.sleep(1)
            progress.update(1)

    logger.info(f"Finished waiting.")


def main(start_time: datetime, end_time: datetime) -> int:

    schedule(start_time, end_time)

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
        ndi.find_wait_for_sources(ndi_find, 5000)
        sources = ndi.find_get_current_sources(ndi_find)
        print(sources[0].ndi_name)

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
        p = Process(target=ndi_receiver_process, args=(source, idx, out_path, stop_event))
        processes.append(p)
        p.start()

    ndi.find_destroy(ndi_find)

    try:
        delta_time = int((end_time - start_time).total_seconds())
        with tqdm(total=delta_time, bar_format="{l_bar}{bar} [Elapsed: {elapsed}, Remaining: {remaining}]") as progress:
            for _ in range(delta_time):
                time.sleep(1)
                progress.update(1)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Terminating processes...")

    finally:
        stop_event.set()
        for process in processes:
            if process.is_alive():
                process.join()

        proc_pano.kill()

    logger.info("Finished recording.")

    return 0


def parse_arguments(args) -> Tuple[datetime]:

    now = datetime.now()

    start_time = now
    if args.start_time:
        splt = args.start_time.split("_")
        if len(splt) == 1:
            h, m = splt[0].split(":")
            start_time = datetime.strptime(f"{now.year}.{now.month}.{now.day}_{h}:{m}", "%Y.%m.%d_%H:%M")
        else:
            start_time = datetime.strptime(args.start_time, "%Y.%m.%d_%H:%M")

    end_time = None
    if args.end_time:
        splt = args.end_time.split("_")
        if len(splt) == 1:
            h, m = splt[0].split(":")
            end_time = datetime.strptime(f"{now.year}.{now.month}.{now.day}_{h}:{m}", "%Y.%m.%d_%H:%M")
        else:
            end_time = datetime.strptime(args.start_time, "%Y.%m.%d_%H:%M")
    elif args.time:
        duration = datetime.strptime(args.time, "%H:%M").time()
        end_time = start_time + timedelta(hours=duration.hour, minutes=duration.minute)
    else:
        duration = datetime.strptime("01:45", "%H:%M").time()
        end_time = start_time + timedelta(hours=duration.hour, minutes=duration.minute)

    return start_time, end_time


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="NDI Stream Recorder", description="Schedule a script to run based on time.")

    parser.add_argument("--start_time", type=str, help="Start time in HH:MM format. e.g. (18:00)", required=False)
    parser.add_argument("--end_time", type=str, help="End time in HH:MM format. e.g. (18:00)", required=False)
    parser.add_argument("--time", type=str, help="Duration in HH:MM format. e.g. (18:00)", required=False)

    args = parse_arguments(parser.parse_args())

    main(*args)
