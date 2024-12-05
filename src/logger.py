import logging
import os
from datetime import datetime

LOG_DIR = f"{os.getcwd()}/output/{datetime.now().strftime('%Y%m%d_%H%M')}"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("ndi_logger")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler(f"{LOG_DIR}/run.log", mode="w")
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    fmt="{asctime} - [{levelname}]: {message}",
    style="{",
)

console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)
