from typing import Callable, AsyncIterable

import disnake
import logging


class Handler:
    _logger = logging.getLogger(__name__)
    _reddit_function = None

    async def stream_reddit_items(self, subreddit):
        self._logger.info(f"Starting to fetch items for {self.__class__.__name__}")
        reddit_function: Callable[[], AsyncIterable] = self._get_reddit_stream_function(subreddit)
        async for item in reddit_function():
            yield item

        self._logger.info(f"Finished fetching items for {self.__class__.__name__}")

    def _get_reddit_stream_function(self, subreddit) -> Callable[[], AsyncIterable]:
        pass

    async def create_embed(self, item) -> disnake.Embed:
        pass

    def should_handle(self, item) -> bool:
        return True

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


