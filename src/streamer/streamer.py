import asyncio
import logging

from asyncpraw.exceptions import AsyncPRAWException


class Streamer:

    def __init__(self, name, _stream_items):
        self._logger = logging.getLogger(name)
        self._stream_items = _stream_items
        self.handlers = []

    async def start(self):
        while True:
            self._logger.info(f"Starting to fetch items")
            try:
                await asyncio.wait_for(self._stream(), timeout=60*60)
            except AsyncPRAWException:
                self._logger.exception(f"Ignoring exception - sleeping instead:")
            except asyncio.TimeoutError:
                self._logger.info(f"Aborting")
            except Exception:
                self._logger.exception(f"ignoring")

            self._logger.info(f"sleeping")
            await asyncio.sleep(10)
            self._logger.info(f"running again")

    async def _stream(self):
        async for item in self._stream_items(skip_existing=True):
            for handler in self.handlers:
                await handler.take(item)

    def add_handler(self, handler):
        self.handlers.append(handler)
        return self
