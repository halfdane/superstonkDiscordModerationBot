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
            current_task = asyncio.current_task()
            self._logger.info(f"[{current_task.get_name()}] Starting to fetch items for {self.__class__.__name__}")
            try:
                await self.handle(report_channels)
            except AsyncPRAWException:
                self._logger.exception(f"[{current_task.get_name()}] Ignoring exception - sleeping instead:")

            await asyncio.sleep(300)

    async def handle(item, channels):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


