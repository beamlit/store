import logging

from common.bl_config import BL_CONFIG


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[1;36m",  # Cyan
        "INFO": "\033[1;32m",  # Green
        "WARNING": "\033[1;33m",  # Yellow
        "ERROR": "\033[1;31m",  # Red
        "CRITICAL": "\033[1;41m",  # Red background
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, "\033[0m")
        record.levelname = f"{color}{record.levelname}\033[0m"
        return super().format(record)


def init():
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False

    level = BL_CONFIG["log_level"]
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter("%(levelname)s:\t  %(name)s - %(message)s"))
    logging.basicConfig(level=level, handlers=[handler])
