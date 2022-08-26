import logging

from helper.item_helper import permalink
from reddit_item_handler import Handler


class RestickyQualityVoteBot(Handler):
    def __init__(self, qvbot_reddit, superstonk_moderators, **kwargs):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.qvbot_reddit = qvbot_reddit
        self.superstonk_moderators = superstonk_moderators

    def wot_doing(self):
        return "Re-sticky QV comment if a mod responds 'sticky'"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.warning(self.wot_doing())

    async def take(self, comment):
        body = getattr(comment, 'body', "")
        author = getattr(getattr(comment, "author", None), "name", None)
        if (author in self.superstonk_moderators) and "sticky" in body.lower():
            parent = await comment.parent()
            await parent.load()
            myself = await self.qvbot_reddit.user.me()
            is_qv_comment = author(parent) == myself.name
            if is_qv_comment:
                sticky = await self.qvbot_reddit.comment(parent.id)
                self._logger.info(f"re-stickying qv comment: {permalink(sticky)}")
                await sticky.mod.distinguish(how="yes", sticky=True)
