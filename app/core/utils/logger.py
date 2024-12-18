import logging
from datetime import datetime

from .dir_creator import get_api_dir, get_recording_dir


def get_recording_logger(start_time: datetime) -> logging.Logger:
    date_str = f"{start_time.astimezone().strftime('%Y%m%d_%H%M')}"
    logger_name = f"ndi_recording_{date_str}"

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    dir_path = get_recording_dir(date_str)
    file_handler = logging.FileHandler(f"{dir_path}/run.log", mode="w")
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="{asctime} - [{levelname}]: {message}",
        style="{",
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_api_logger() -> logging.Logger:
    date_str = f"{datetime.now().strftime('%Y%m%d_%H%M')}"
    logger_name = f"api_{date_str}"

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    api_dir = get_api_dir()
    file_handler = logging.FileHandler(f"{api_dir}/{date_str}.log", mode="w")
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="{asctime} - [{levelname}]: {message}",
        style="{",
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
