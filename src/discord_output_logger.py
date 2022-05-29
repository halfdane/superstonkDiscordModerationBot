import asyncio
import logging
from datetime import datetime


class DiscordOutputLogger(logging.Handler):
    log_lines = []

    def __init__(self):
        logging.Handler.__init__(self)
        self.logging_output_channel = None
        self.asyncio_loop = None
        self.scheduler = None

    async def on_ready(self, logging_output_channel, asyncio_loop, scheduler, **kwargs):
        self.logging_output_channel = logging_output_channel
        self.asyncio_loop = asyncio_loop
        self.scheduler = scheduler
        scheduler.add_job(self.loglines_to_discord, "cron", second="*/5", next_run_time=datetime.now())

    def emit(self, record):
        message = self.format(record)
        self.log_lines.append(message)

    def get_conc_messages(self):
        lines = self.log_lines
        self.log_lines = []

        message = ""
        for line in lines:
            # Add the line to the message if it doesn't make it to large
            if len(message) + len(line) + 4 > 2000:
                yield message
                message = ""
            message += line + '\n   '

        if len(message) > 0:
            yield message

    async def loglines_to_discord(self):
        for content in self.get_conc_messages():
            try:
                msg = await self.logging_output_channel.send(content=content)
                await msg.edit(suppress=True)
            except Exception:
                self.handleError(content)
