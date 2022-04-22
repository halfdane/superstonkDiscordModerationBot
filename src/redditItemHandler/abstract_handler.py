import asyncio
import logging
from asyncpraw.exceptions import AsyncPRAWException


class Handler:

    def __init__(self, bot):
        self.bot = bot
        self._logger = logging.getLogger(self.__class__.__name__)

    async def start(self):
        while True:
            self._logger.info(f"Starting to fetch items")
            try:
                await asyncio.wait_for(self.handle(), timeout=60*60)
            except AsyncPRAWException:
                self._logger.exception(f"Ignoring exception - sleeping instead:")
            except asyncio.TimeoutError:
                self._logger.info(f"Aborting")
            except Exception:
                self._logger.exception(f"ignoring")

            self._logger.info(f"sleeping")
            await asyncio.sleep(10)
            self._logger.info(f"running again")

    async def handle(self):
        pass

    async def is_new_item(self, channel, item):
        for message in await channel.history(limit=10).flatten():
            existing_item = await self.bot.get_item(message)
            existing_item_id = existing_item.id if existing_item is not None else None
            self._logger.debug(f"is {item.id} == {existing_item_id}? {item.id == existing_item_id}")
            if item.id == existing_item_id:
                return False
        return True

    def __repr__(self):
        return self.__class__.__name__


