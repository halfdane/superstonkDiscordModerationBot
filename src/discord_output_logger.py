import asyncio
import logging


class DiscordOutputLogger(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)
        self.logging_output_channel = None
        self.asyncio_loop = None

    async def on_ready(self, logging_output_channel, asyncio_loop, **kwargs):
        self.logging_output_channel = logging_output_channel
        self.asyncio_loop = asyncio_loop

    def emit(self, record):
        if self.logging_output_channel is None or self.asyncio_loop is None:
            return

        try:
            self.asyncio_loop.create_task(self.async_emit(record))
        except Exception:
             self.handleError(record)

    async def async_emit(self, record):
        try:
            message = self.format(record)
            msg = await self.logging_output_channel.send(content=message)
            await msg.edit(suppress=True)
        except Exception:
            self.handleError(record)
