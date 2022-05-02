import logging


def permalink(item):
    return f"https://www.reddit.com{item.permalink}"


class Handler:

    def __init__(self, bot):
        self.bot = bot
        self._logger = logging.getLogger(self.__class__.__name__)

    async def take(self, item):
        pass

    async def on_ready(self):
        pass

    async def _was_recently_posted(self, item, channel):
        async for elem in channel \
                .history(limit=200) \
                .filter(lambda message: message.author.id == self.bot.user.id):
            if self.permalink(item) == elem.embeds[0].url:
                return True
        return False
