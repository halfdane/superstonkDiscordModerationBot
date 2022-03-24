from typing import Callable, AsyncIterable

import disnake
import logging

class BoundedSet:
    """
    A set with a maximum size that evicts the oldest items when necessary.
    This class does not implement the complete set interface.
    """

    def __init__(self, max_items: int):
        """Construct an instance of the BoundedSet."""
        self.max_items = max_items
        self._list = list()
        self._set = set()

    def __contains__(self, item) -> bool:
        """Test if the BoundedSet contains item."""
        return item in self._set

    def add(self, item):
        """Add an item to the set discarding the oldest item if necessary."""
        if len(self._set) == self.max_items:
            self._set.remove(self._list.pop(0))
        self._list.append(item)
        self._set.add(item)


class Handler:
    _logger = logging.getLogger(__name__)
    _id_cache = BoundedSet(301)
    _reddit_function = None

    async def stream_reddit_items(self, subreddit):
        self._logger.info(f"Starting to fetch items for {self.__class__.__name__}")
        reddit_function: Callable[[], AsyncIterable] = self._get_reddit_stream_function(subreddit)
        async for item in reddit_function():
            if not item:
                continue
            if item.id in self._id_cache:
                continue
            self._id_cache.add(item.id)
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


