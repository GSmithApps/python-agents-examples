from logging import Logger
import contextlib
class MyLogger:

    def __init__(self, logger: Logger):
        self._logger = logger
        self._depth = 0

    def info(self, mystring: str):
        self._logger.info(f"{' ' * self._depth * 2}🟢 \033[32m{mystring}\033[0m 🟢")

    @contextlib.contextmanager
    def scope(self):
        self._depth += 1
        try:
            yield
        finally:
            self._depth -= 1    
