import argparse
import os
import subprocess
import time
from datetime import datetime, timedelta
from multiprocessing import Event, Process
from typing import Tuple
from PIL import Image

import onnxruntime
import torch
import torchvision.transforms as T
from tqdm import tqdm

from src.camera_system import CameraSystem
from src.logger import LOG_DIR, logger
from src.utils import Camera, CameraOrientation


def rtsp_process(
    camera_system: CameraSystem,
    camera: Camera,
    stop_event: Event,
    frame_size: Tuple[int],
    onnx_file: str,
    fps: int = 15,
):
    onnx_session = onnxruntime.InferenceSession(onnx_file)
    logger.info(f"ONNX Model Device: {onnxruntime.get_device()}")

    transform = T.Compose(
        [
            T.Resize((640, 640)),
            T.ToTensor(),
        ]
    )

    orig_size = torch.tensor([frame_size[0], frame_size[1]])[None].to('cuda')

    try:
        while not stop_event.is_set():
            frame = camera_system.get_frame(camera).get_frame()
            if frame is not None:
                img = transform(Image.fromarray(frame))[None].to('cuda')

                labels, boxes, scores = onnx_session.run(
                    output_names=None,
                    input_feed={
                        'images': img.data.numpy(),
                        "orig_target_sizes": orig_size.data.numpy(),
                    },
                )

                bucket_width = 716
                buckets = {1: [], 2: [], 3: []}

                bboxes_player = boxes[(labels == 2) & (scores > 0.5)]
                centers_x = (bboxes_player[:, 0] + bboxes_player[:, 2]) / 2 - 350

                for i, center_x in enumerate(centers_x):
                    if center_x < bucket_width:  # Left region
                        buckets[1].append(bboxes_player[i])
                    elif center_x < 2 * bucket_width:  # Middle region
                        buckets[2].append(bboxes_player[i])
                    else:  # Right region
                        buckets[3].append(bboxes_player[i])

                most_populated_bucket = max(buckets, key=lambda k: len(buckets[k]))

                camera_system.change_orientation(CameraOrientation(most_populated_bucket))

            else:
                logger.warning(f"No panorama frame captured.")
    except KeyboardInterrupt:
        camera_system.cameras[camera].stop()

    logger.info(f"RTSP Receiver Process stopped.")


def ndi_process(camera_system: CameraSystem, camera: Camera, path: str, stop_event: Event, codec: str = "h264_nvenc"):

    ffmpeg_process = subprocess.Popen(
        [
            "ffmpeg",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "yuv420p",
            "-s",
            "1920x1080",
            "-r",
            str(camera_system.cameras[camera].fps),
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
            "-hwaccel",
            "cuda",
            "-hwaccel_output_format",
            "cuda",
            os.path.join(path, f"cam{camera.value}.mp4"),
        ],
        stdin=subprocess.PIPE,
    )

    try:
        while not stop_event.is_set():
            frame, t = camera_system.get_frame(camera)
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
    camera_system = CameraSystem()

    processes = []
    stop_event = Event()
    for camera in camera_system.cameras:
        if camera != Camera.PANO:
            p = Process(target=ndi_process, args=(camera_system, camera, LOG_DIR, stop_event))
        else:
            p = Process(target=rtsp_process, args=(camera_system, camera, LOG_DIR, stop_event))
        processes.append(p)
        p.start()

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
