import logging


class Reaction:
    emoji = None

    def __init__(self, **_):
        self._logger = logging.getLogger(self.__class__.__name__)

    async def handle_reaction(self, message, emoji, user, channel):
        pass

    async def unhandle_reaction(self, message, emoji, user, channel):
        pass

    @staticmethod
    def description():
        pass
