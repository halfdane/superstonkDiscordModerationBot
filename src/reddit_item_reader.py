import asyncio
import logging
from datetime import datetime

from asyncpraw.exceptions import AsyncPRAWException

AN_HOUR = 60 * 60
TEN_SECONDS = 10


class RedditItemReader:

    def __init__(self, name, item_fetch_function, item_repository, handlers):
        self._logger = logging.getLogger(name)
        self.name = name
        self.item_fetch_function = item_fetch_function
        self.item_repository = item_repository
        self.handlers = handlers

    async def on_ready(self, scheduler, **kwargs):
        for handler in self.handlers:
            await handler.on_ready(**dict(kwargs, scheduler=scheduler))
        self._logger.info(f"Ready to fetch {self.name} every few seconds")
        scheduler.add_job(self._stream_until_timeout, 'interval', seconds=AN_HOUR + TEN_SECONDS, next_run_time=datetime.now())

    async def _stream_until_timeout(self):
        self._logger.info(f"Streaming")
        try:
            await asyncio.wait_for(self._stream(), timeout=AN_HOUR)
        except asyncio.TimeoutError:
            self._logger.info(f"Aborting")

    async def _stream(self):
        async for item in self.item_fetch_function():
            if not (await self.item_repository.contains(item)):
                for handler in self.handlers:
                    await handler.take(item)
            await self.item_repository.store([item])
