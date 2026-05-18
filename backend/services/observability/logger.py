import logging
import os
from dotenv import load_dotenv
from logtail import LogtailHandler

load_dotenv()

SOURCE_TOKEN = os.getenv("BETTERSTACK_SOURCE_TOKEN")

handler = LogtailHandler(source_token=SOURCE_TOKEN)

logger = logging.getLogger("ams-backend")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(handler)


def log_info(message: str, extra: dict = None):
    logger.info({
        "message": message,
        "extra": extra or {}
    })


def log_error(message: str, extra: dict = None):
    logger.error({
        "message": message,
        "extra": extra or {}
    })