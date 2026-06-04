import logging
import os
import re
from logging.handlers import RotatingFileHandler


def parse_drop_data(data: str) -> list:
    paths = []
    if "{" in data:
        paths = re.findall(r"\{([^}]+)\}", data)
        rest = re.sub(r"\{[^}]+\}", "", data).strip()
        if rest:
            paths.extend(rest.split())
    else:
        paths = data.split()
    return [p for p in paths if os.path.exists(p)]


def setup_logging():
    handler = RotatingFileHandler(
        "convertidor.log",
        maxBytes=1 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
