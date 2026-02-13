import os
import logging
from app.utils.logger import setup_logging


def test_logger_setup():
    setup_logging()
    assert os.path.exists("logs")
    assert os.path.exists("logs/fake_news_pipeline.log")

    logger = logging.getLogger("test_logger")
    assert logger.level == logging.NOTSET  # Default level if not set specific
