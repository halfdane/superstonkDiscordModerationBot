import asyncio
from typing import Callable, AsyncIterable
from disnake import Message

import disnake
import logging

import discordReaction


class Handler:
    _logger = logging.getLogger(__name__)

    def __init__(self, _reddit, _subreddit):
        self._reddit = _reddit
        self._subreddit = _subreddit

    async def start(self, report_channels):
        reddit_function: Callable[[], AsyncIterable] = self._get_reddit_stream_function(self._subreddit)
        while True:
            self._logger.info(f"Starting to fetch items for {self.__class__.__name__}")
            try:
                async for item in reddit_function():
                    await self.handle(item, report_channels)
            except Exception:
                self._logger.exception(f"Ignoring exception - sleeping instead:")
                await asyncio.sleep(10)



    def _get_reddit_stream_function(self, subreddit) -> Callable[[], AsyncIterable]:
        pass

    async def create_embed(self, item) -> disnake.Embed:
        pass

    async def handle(self, item, channels):
        embed = await self.create_embed(item)
        for channel in channels:
            msg: Message = await channel.send(embed=embed)
            await discordReaction.add_reactions(msg)

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


