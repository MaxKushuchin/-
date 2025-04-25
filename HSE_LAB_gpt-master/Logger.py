# Logger.py
import logging
import sys
from typing import Any


class Logger:
    def __init__(self, name: str = "CodeProcessor"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Консольный обработчик
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # Файловый обработчик
        fh = logging.FileHandler('app.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def info(self, message: str, *args: Any) -> None:
        self.logger.info(message, *args)

    def warning(self, message: str, *args: Any) -> None:
        self.logger.warning(message, *args)

    def error(self, message: str, *args: Any) -> None:
        self.logger.error(message, *args)

    def debug(self, message: str, *args: Any) -> None:
        self.logger.debug(message, *args)


# Глобальный экземпляр логгера
logger = Logger().logger