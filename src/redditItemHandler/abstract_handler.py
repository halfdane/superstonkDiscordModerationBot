import logging


def permalink(item):
    return f"https://www.reddit.com{item.permalink}"


async def was_recently_posted(item, channel, discord_bot_user):
    async for elem in channel \
            .history(limit=200) \
            .filter(lambda message: message.author.id == discord_bot_user.id):
        if len(getattr(elem, 'embeds', [])) > 0 and permalink(item) == elem.embeds[0].url:
            return True
    return False


class Handler:

    def __init__(self, bot):
        self.bot = bot
        self._logger = logging.getLogger(self.__class__.__name__)

    async def take(self, item):
        pass

    async def on_ready(self):
        pass

