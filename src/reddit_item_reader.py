import asyncio
import logging

from asyncpraw.exceptions import AsyncPRAWException


class RedditItemReader:
    def __init__(self, name, item_fetch_function, item_repository, handlers):
        self._logger = logging.getLogger(name)
        self.name = name
        self.item_fetch_function = item_fetch_function
        self.item_repository = item_repository
        self.handlers = handlers

    async def on_ready(self, scheduler, **kwargs):
        for handler in self.handlers:
            await handler.on_ready()
        self._logger.info(f"Ready to fetch {self.name} every few seconds")
        scheduler.add_job(self._stream, "cron", second="*/30")

    async def _stream(self):
        async for item in self.item_fetch_function():
            if not (await self.item_repository.contains(item)):
                for handler in self.handlers:
                    await handler.take(item)
            await self.item_repository.store([item])
