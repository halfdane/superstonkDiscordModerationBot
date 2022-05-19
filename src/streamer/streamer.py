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
                await asyncio.wait_for(self._stream(), timeout=10 * 60)
            except AsyncPRAWException:
                self._logger.exception(f"Ignoring exception - sleeping instead:")
            except asyncio.TimeoutError:
                self._logger.info(f"Aborting")
            except Exception:
                self._logger.exception(f"ignoring")
            await asyncio.sleep(1)

    async def _stream(self):
        async for item in self.input_stream_function():
            for handler in self.handlers:
                await handler.take(item)


class Stream:
    def __init__(self, name):
        self.name = name

    def from_input(self, input_stream_function):
        return StreamerWithHandler(name=self.name, input_stream_function=input_stream_function)


class StreamerWithHandler:
    def __init__(self, name, input_stream_function):
        self.name = name
        self.input_stream_function = input_stream_function
        self.handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)
        return self

    def start(self, asyncio_loop, **kwargs):
        streamer = ActualStreamer(name=self.name, input_stream_function=self.input_stream_function, handlers=self.handlers)
        streamer.start(asyncio_loop)
