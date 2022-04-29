import asyncio
import logging
from datetime import datetime, timedelta

from asyncpraw.exceptions import AsyncPRAWException


class ActualStreamer:
    def __init__(self, name, input_stream_function, handlers):
        self._logger = logging.getLogger(name)
        self.input_stream_function = input_stream_function
        self.handlers = handlers

    def start(self, asyncio_loop):
        asyncio_loop.create_task(self._loop())

    async def _loop(self):
        for handler in self.handlers:
            await handler.on_ready()

        while True:
            self._logger.info(f"Starting to fetch items")
            try:
                await asyncio.wait_for(self._stream(), timeout=3 * 60 * 60)
            except AsyncPRAWException:
                self._logger.exception(f"Ignoring exception - sleeping instead:")
            except asyncio.TimeoutError:
                self._logger.info(f"Aborting")
            except Exception:
                self._logger.exception(f"ignoring")

            self._logger.info(f"sleeping")
            await asyncio.sleep(1)
            self._logger.info(f"running again")

    async def _stream(self):
        async for item in self.input_stream_function():
            for handler in self.handlers:
                await handler.take(item)


class StreamBase:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class Stream(StreamBase):
    def __init__(self, name):
        super().__init__(name=name)

    def from_input(self, input_stream_function):
        return StreamerWithHandler(input_stream_function=input_stream_function, **self.kwargs)

class StreamerWithHandler(StreamBase):
    def with_handlers(self, handlers):
        return ActualStreamer(handlers=handlers, **self.kwargs)
