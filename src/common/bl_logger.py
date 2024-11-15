import logging
import os


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[1;36m',    # Cyan
        'INFO': '\033[1;32m',     # Green
        'WARNING': '\033[1;33m',  # Yellow
        'ERROR': '\033[1;31m',    # Red
        'CRITICAL': '\033[1;41m'  # Red background
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, '\033[0m')
        record.levelname = f"{color}{record.levelname}\033[0m"
        return super().format(record)

def init():
    level = os.getenv('LOG_LEVEL', os.getenv('BL_LOG_LEVEL', logging.DEBUG))
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter('%(levelname)s:\t  %(name)s - %(message)s'))
    logging.basicConfig(
        level=level,
        handlers=[handler]
    )
