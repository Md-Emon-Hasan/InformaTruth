import logging
import sys
import os
from config import LOG_FORMAT
from config import LOG_LEVEL


def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(log_dir, "fake_news_pipeline.log")),
        ],
    )

    # Configure library log levels
    logging.getLogger("newspaper").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("langgraph").setLevel(logging.INFO)
    logging.getLogger("duckduckgo_search").setLevel(logging.WARNING)
