import asyncio
import logging
from asyncpraw.exceptions import AsyncPRAWException


class Handler:
    _logger = logging.getLogger(__name__)

    def __init__(self, _reddit, _subreddit):
        self._reddit = _reddit
        self._subreddit = _subreddit

    async def start(self, report_channels):
        while True:
            self._current_task = asyncio.current_task()
            self._logger.info(f"[{self._current_task.get_name()}] Starting to fetch items for {self.__class__.__name__}")
            try:
                await asyncio.wait_for(self.handle(report_channels), timeout=60*60)
            except AsyncPRAWException:
                self._logger.exception(f"[{self._current_task.get_name()}] Ignoring exception - sleeping instead:")
            except asyncio.TimeoutError:
                self._logger.info(f"Aborting [{self._current_task.get_name()}]")

            self._logger.info(f"[{self._current_task.get_name()}] sleeping")
            await asyncio.sleep(10)
            self._logger.info(f"[{self._current_task.get_name()}] running again")

    async def handle(item, channels):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


