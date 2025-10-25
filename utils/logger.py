import logging
import os
from datetime import datetime
from pathlib import Path


class Logger:
    _instances = {}

    @staticmethod
    def get_logger(name: str):
        if name not in Logger._instances:
            Logger._instances[name] = Logger._create_logger(name)
        return Logger._instances[name]

    @staticmethod
    def _create_logger(name: str):
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        if logger.handlers:
            return logger

        file_handler = logging.FileHandler(
            logs_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger
