import logging

class Reaction:
    emoji = None

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    async def handle(self, message, item, emoji, user, channel, bot):
        pass

    async def unhandle(self, message, item, emoji, user, channel, bot):
        pass

    def is_reaction(self, message, item, e, user, channel, bot):
        return e == self.emoji

    def description(self):
        pass
