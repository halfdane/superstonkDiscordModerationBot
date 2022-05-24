import logging


class Handler:

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    async def take(self, item):
        pass

    async def on_ready(self):
        pass

