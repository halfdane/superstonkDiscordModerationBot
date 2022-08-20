import asyncio
from random import randint

from helper.links import permalink
from reddit_item_handler import Handler


class FrontDeskSticky(Handler):
    _sticky_text = """**G**ooooood **M**orning **E**veryone!

# The Front Desk is open!

Our ape historian u/Elegant-Remote6667 asks for help: https://www.reddit.com/r/Superstonk/comments/wt45ph/

Tldr: can you see the post behind this ipfs link? https://bafybeibwxpaduwd5kxj6vmfbdetooemcxqpnuscqmk3s7ydj7bmim7jvge.ipfs.w3s.link/wssqzb_Superstonk_post.html
"""

    def __init__(self, **kwargs):
        super().__init__()

    def wot_doing(self):
        return "Create Front Desk comments"

    async def on_ready(self, **kwargs):
        self._logger.warning(self.wot_doing())

    async def take(self, item):
        if await self.needs_front_desk(item):
            await asyncio.sleep(randint(30, 600))
            self._logger.info(f"No Front Desk -- adding it now")
            front_desk = await item.reply(self._sticky_text)
            await front_desk.mod.distinguish(how='yes', sticky=True)

    async def needs_front_desk(self, item):
        if getattr(getattr(item, "author", None), "name", None) == "AutoModerator" and \
                "$GME Daily Directory" in item.title:
            self._logger.info(f"Found the daily: {permalink(item)}")
            await item.load()
            for c in item.comments:
                if getattr(getattr(c, "author", None), "name", None) == "half_dane" and \
                        "The Front Desk is open!" in c.body:
                    self._logger.info(f"Found the Front Desk: {permalink(c)}")
                    return False
            return True

        return False
