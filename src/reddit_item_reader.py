import asyncio
import logging
from datetime import datetime

TEN_MINUTES = 10 * 60
TEN_SECONDS = 10


class RedditItemReader:

    def __init__(self, name, item_fetch_function, item_repository, handlers):
        self._logger = logging.getLogger(name)
        self.name = name
        self.item_fetch_function = item_fetch_function
        self.item_repository = item_repository
        self.handlers = handlers

    def wot_doing(self):
        return f"[internal] Reading {self.name} every few seconds"

    async def on_ready(self, scheduler, **kwargs):
        scheduler.add_job(self._stream_until_timeout, 'interval', seconds=TEN_MINUTES + TEN_SECONDS, next_run_time=datetime.now())

    async def _stream_until_timeout(self):
        try:
            await asyncio.wait_for(self._stream(), timeout=TEN_MINUTES)
        except (asyncio.TimeoutError, asyncio.exceptions.CancelledError, asyncio.exceptions.TimeoutError):
            pass

    async def _stream(self):
        async for item in self.item_fetch_function():

            needs_handling = (self.item_repository is None) or (not (await self.item_repository.contains(item)))
            if needs_handling:
                for handler in self.handlers:
                    try:
                        finished_handling = await handler.take(item)
                        if finished_handling:
                            break
                    except Exception as e:
                        self._logger.exception(f"Caught an exception in {handler}:")

            if self.item_repository is not None:
                await self.item_repository.store([item])
