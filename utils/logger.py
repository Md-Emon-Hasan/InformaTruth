import logging
import sys
from config import LOG_FORMAT
from config import LOG_LEVEL

def setup_logging():
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("fake_news_pipeline.log")
        ]
    )
    
    # Configure library log levels
    logging.getLogger("newspaper").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("langgraph").setLevel(logging.INFO)
    logging.getLogger("duckduckgo_search").setLevel(logging.WARNING)