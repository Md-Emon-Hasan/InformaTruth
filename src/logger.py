# ========================================
# 🧱 logger.py — Logger Setup (Industry-Grade)
# ========================================
import logging
import os
from config import LOG_FILE_PATH

def setup_logger(name):
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)

    # Stream handler
    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(stream_formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger