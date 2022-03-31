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

    async def stream_reddit_items(self):
        self._logger.info(f"Starting to fetch items for {self.__class__.__name__}")
        reddit_function: Callable[[], AsyncIterable] = self._get_reddit_stream_function(self._subreddit)
        async for item in reddit_function():
            yield item

        self._logger.info(f"Finished fetching items for {self.__class__.__name__}")

    def _get_reddit_stream_function(self, subreddit) -> Callable[[], AsyncIterable]:
        pass

    async def create_embed(self, item) -> disnake.Embed:
        pass

    async def handle(self, item, channels):
        embed = await self.create_embed(item)
        for channel in channels:
            msg: Message = await channel.send(embed=embed)
            await discordReaction.add_reactions(msg)

    def should_handle(self, item) -> bool:
        return True

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


