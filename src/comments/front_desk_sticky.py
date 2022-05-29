import asyncio
from random import randint

from redditItemHandler import Handler
from helper.links import permalink


class FrontDeskSticky(Handler):
    _sticky_text = """**G**ooooood **M**orning **E**veryone!

# The Front Desk is open!

[Computershare Megathread](https://www.reddit.com/r/Superstonk/comments/ugnqsg/drscomputershare_megathread_052022) || 
[Join our Superstonk Discord](https://discord.gg/superstonk) || 
[Voting Megathread](https://www.reddit.com/r/Superstonk/comments/uddedr)

# [SUPPORT FOR THE GAMESTOP WALLET](https://support.blockchain.gamestop.com/hc/en-us/sections/4412111751955-Getting-Started) 

*Please don't just blindly trust people that approach you in DMs*! 
We have received several reports of people who lost money to someone who claimed to help!
"""

    def __init__(self, **kwargs):
        super().__init__()

    async def on_ready(self, **kwargs):
        self._logger.info("Ready to create a fresh Front Desk")

    async def take(self, item):
        if await self.needs_front_desk(item):
            await asyncio.sleep(randint(30, 600))
            self._logger.info(f"No Front Desk -- adding it now")
            front_desk = await item.reply(self._sticky_text)
            await front_desk.mod.distinguish(how='yes', sticky=True)

    async def needs_front_desk(self, item):
        if getattr(getattr(item, "author", None), "name", None) == "AutoModerator" and \
                item.title == "| $GME Daily Discussion | New to the sub? Start here!":
            self._logger.info(f"Found the daily: {permalink(item)}")
            await item.load()
            for c in item.comments:
                if getattr(getattr(c, "author", None), "name", None) == "half_dane" and \
                        "The Front Desk is open!" in c.body:
                    self._logger.info(f"Found the Front Desk: {permalink(c)}")
                    return False
            return True

        return False
