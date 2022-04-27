import logging
from datetime import datetime, timedelta


class Handler:

    def __init__(self, bot):
        self.bot = bot
        self._logger = logging.getLogger(self.__class__.__name__)

    async def take(self, item):
        pass

    async def _was_recently_posted(self, item, channel):
        an_hour_ago = datetime.now() - timedelta(hours=1)
        async for elem in channel \
                .history(after=an_hour_ago) \
                .filter(lambda message: message.author.id == self.bot.user.id):
            if self.permalink(item) == elem.embeds[0].url:
                return True
        return False

    def permalink(self, comment):
        return f"https://www.reddit.com{comment.permalink}"
