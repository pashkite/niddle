from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class UTCFormatter(logging.Formatter):
    converter = datetime.utcfromtimestamp

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


def setup_logger(name: str, level: str, log_dir: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    formatter = UTCFormatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(Path(log_dir) / "engine.log")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def get_logger(name: str, level: Optional[str] = None, log_dir: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if level and log_dir:
        return setup_logger(name, level, log_dir)
    return logger
