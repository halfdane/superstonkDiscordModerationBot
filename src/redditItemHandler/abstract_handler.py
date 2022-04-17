import asyncio
import logging
from asyncpraw.exceptions import AsyncPRAWException


class Handler:
    _logger = logging.getLogger(__name__)

    def __init__(self, bot):
        self.bot = bot
        self._current_task = None

    async def start(self):
        while True:
            self._current_task = asyncio.current_task()
            self._logger.info(f"[{self._current_task.get_name()}] Starting to fetch items for {self.__class__.__name__}")
            try:
                await asyncio.wait_for(self.handle(), timeout=60*60)
            except AsyncPRAWException:
                self._logger.exception(f"[{self._current_task.get_name()}] Ignoring exception - sleeping instead:")
            except asyncio.TimeoutError:
                self._logger.info(f"Aborting [{self._current_task.get_name()}]")
            except Exception:
                self._logger.exception(f"[{self._current_task.get_name()}] ignoring")

            self._logger.info(f"[{self._current_task.get_name()}] sleeping")
            await asyncio.sleep(10)
            self._logger.info(f"[{self._current_task.get_name()}] running again")

    async def handle(self):
        pass

    async def is_new_item(self, channel, item):
        for message in await channel.history(limit=10).flatten():
            existing_item = await self.bot.get_item(message)
            if existing_item and item.id == existing_item.id:
                return False

        return True

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


