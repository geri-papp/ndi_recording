import argparse
import os
import subprocess
import time
from collections import Counter, deque
from datetime import datetime, timedelta
from multiprocessing import Event, Process
from typing import Tuple

import cv2
import numpy as np
import onnxruntime
import time

from typing import List
from tqdm import tqdm

from src.logger import LOG_DIR, logger
import src.cameras.ptz as ptz
from src.cameras.ptz import CameraPTZ
from src.cameras.pano import CameraPano
from src.utils import CameraOrientation


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
    camera: CameraPano, ptz_cameras: List[CameraPTZ], onnx_file: str, stop_event: Event, start_event: Event
):
    """ """

    sleep_time = 1 / camera.fps
    bucket_width = camera.frame_size[1] // 3

    onnx_session = onnxruntime.InferenceSession(onnx_file, providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
    logger.info(f"ONNX Model Device: {onnxruntime.get_device()}")

    window = deque()
    freq_counter = Counter()

    start_event.set()
    try:
        while not stop_event.is_set():
            frame = camera.get_frame()

            if frame is None:
                logger.warning(f"No panorama frame captured.")
                continue

            img = cv2.resize(frame, (640, 640), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
            img = np.expand_dims(np.transpose(img, (2, 0, 1)), axis=0)

            labels, boxes, scores = onnx_session.run(
                output_names=None,
                input_feed={
                    'images': img,
                    "orig_target_sizes": camera.frame_size[::-1],
                },
            )

            most_populated_bucket = process_buckets(boxes, labels, scores, bucket_width)
            mode = update_frequency(window, freq_counter, most_populated_bucket)

            for ptz_cam in ptz_cameras:
                ptz_cam.orientation = CameraOrientation(mode)
            # draw(Image.fromarray(frame), labels, boxes, scores, mode, bucket_width, thrh=0.5)

            time.sleep(sleep_time)

    except KeyboardInterrupt:
        camera.stop()

    logger.info(f"RTSP Receiver Process stopped.")


def ptz_process(camera: CameraPTZ, path: str, stop_event: Event, codec: str = "h264_nvenc"):

    ffmpeg_process = subprocess.Popen(
        [
            "ffmpeg",
            "-hwaccel",
            "cuda",
            "-hwaccel_output_format",
            "cuda",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "yuv420p",
            "-s",
            "1920x1080",
            "-r",
            str(camera.fps),
            "-i",
            "pipe:",
            "-c:v",
            codec,
            "-b:v",
            "30000k",
            "-preset",
            "fast",
            "-profile:v",
            "high",
            os.path.join(path, f"cam{camera.idx}.mp4"),
        ],
        stdin=subprocess.PIPE,
    )

    try:
        while not stop_event.is_set():
            frame, t = camera.get_frame(camera)
            if frame is not None:
                try:
                    ffmpeg_process.stdin.write(frame.tobytes())
                    ffmpeg_process.stdin.flush()
                except BrokenPipeError as e:
                    logger.error(f"Broken pipe error while writing frame: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error in NDI Receiver Process {camera}: {e}")
                    break
            else:
                logger.warning(f"No video frame captured. Frame type: {t}")
    except KeyboardInterrupt:
        ffmpeg_process.stdin.flush()
        ffmpeg_process.stdin.close()

    logger.info(f"NDI Receiver Process {camera} stopped.")


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

    start_event = Event()
    stop_event = Event()

    ndi_sources, ndi_find = ptz.get_sources()
    ptz_cameras = []
    for ndi_source in ndi_sources:
        camera = ptz.CameraPTZ(src=ndi_source, fps=50)
        ptz_cameras.append(camera)

    camera = CameraPano(
        url="/media/geri/88438b12-8823-446e-b364-546efb5da056/datasets/wp_old/videos/tmp.mp4",
        fps=15,
        roi=(420, 1190, 1150, 3390),
    )
    proc_pano = Process(target=pano_process, args=(camera, ptz_cameras, './rtdetrv2.onnx', stop_event, start_event))
    proc_pano.start()

    start_event.wait()
    processes = []
    for camera in ptz_cameras:
        p = Process(target=ptz_process, args=(camera, LOG_DIR, stop_event))
        processes.append(p)
        p.start()

    ptz.find_destroy(ndi_find)

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
            else:
                logger.warning(f"Process {process} not created.")

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
    elif args.duration:
        duration = datetime.strptime(args.duration, "%H:%M").time()
        end_time = start_time + timedelta(hours=duration.hour, minutes=duration.minute)
    else:
        duration = datetime.strptime("01:45", "%H:%M").time()
        end_time = start_time + timedelta(hours=duration.hour, minutes=duration.minute)

    return start_time, end_time


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="NDI Stream Recorder",
        description="Schedule a script to run based on time.",
    )

    parser.add_argument("--start_time", type=str, help="Start time in HH:MM format. e.g. (18:00)", required=False)
    parser.add_argument("--end_time", type=str, help="End time in HH:MM format. e.g. (18:00)", required=False)
    parser.add_argument("--duration", type=str, help="Duration in HH:MM format. e.g. (18:00)", required=False)

    args = parse_arguments(parser.parse_args())

    main(*args)
