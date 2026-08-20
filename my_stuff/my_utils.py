from logging import Logger

class MyLogger:

    def __init__(self, logger: Logger):
        self._logger = logger

    def info(self, mystring: str):
        self._logger.info(f"🟢 \033[32m{mystring}\033[0m 🟢")