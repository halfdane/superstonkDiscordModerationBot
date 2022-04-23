import asyncio
import logging
from asyncpraw.exceptions import AsyncPRAWException


class Handler:

    def __init__(self, bot):
        self.bot = bot
        self._logger = logging.getLogger(self.__class__.__name__)

    async def take(self, item):
        pass

    async def is_new_item(self, channel, item):
        for message in await channel.history(limit=10).flatten():
            existing_item = await self.bot.get_item(message)
            existing_item_id = existing_item.id if existing_item is not None else None
            if item.id == existing_item_id:
                self._logger.info(f"skipping over already existing item: {item.id}")
                return False
        return True

    def __repr__(self):
        return self.__class__.__name__


