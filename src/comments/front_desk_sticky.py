import asyncio
from random import randint

from helper.item_helper import permalink
from reddit_item_handler import Handler
from comments.flairy import flairy_explanation_text


class FrontDeskSticky(Handler):
    def __init__(self, flairy_reddit=None, flairy_reddit_username=None, **kwargs):
        super().__init__()
        self.flairy_reddit = flairy_reddit
        self.flairy_reddit_username = flairy_reddit_username

    def wot_doing(self):
        return "Create Front Desk comments"

    async def take(self, item):
        if await self.needs_front_desk(item):
            self._logger.info(f"No Front Desk -- adding it now")

            daily_from_flairies_view = await self.flairy_reddit.submission(item.id, fetch=False)
            sticky_text = self.front_desk_text(self.flairy_reddit_username)
            front_desk = await daily_from_flairies_view.reply(sticky_text)
            await front_desk.mod.distinguish(how='yes', sticky=True)

    async def needs_front_desk(self, item):
        if getattr(getattr(item, "author", None), "name", None) == "AutoModerator" and \
                "$GME Daily Directory" in item.title:
            self._logger.info(f"Found the daily: {permalink(item)}")
            await item.load()
            for c in item.comments:
                if getattr(getattr(c, "author", None), "name", None) == self.flairy_reddit_username and \
                        "The Front Desk is open!" in c.body:
                    self._logger.info(f"Found the Front Desk: {permalink(c)}")
                    return False
            return True

        return False

    def front_desk_text(self, flairy_username):
        return f"""Good morning Superstonk!   
If you need anything, please tag us by using: `!MODS!` and we will follow up as soon as we are able!

{flairy_explanation_text(flairy_username=flairy_username)}

# The Front Desk is open!

"""
