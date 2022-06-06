import logging

from helper.links import permalink
from redditItemHandler import Handler


class RestickyQualityVoteBot(Handler):
    def __init__(self, qvbot_reddit, is_live_environment, superstonk_moderators, **kwargs):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.qvbot_reddit = qvbot_reddit
        self.superstonk_moderators = superstonk_moderators

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Ready to re-sticky QV comments")

    async def take(self, comment):
        body = getattr(comment, 'body', "")
        author = getattr(getattr(comment, "author", None), "name", None)
        if (author in self.superstonk_moderators) and "sticky" in body:
            parent = await comment.parent()
            myself = await self.qvbot_reddit.user.me()
            is_qv_comment = parent.author.name == myself.name
            if is_qv_comment:
                sticky = await self.qvbot_reddit.comment(parent.id)
                self._logger.info(f"re-stickying qv comment: {permalink(sticky)}")
                await sticky.mod.distinguish(how="yes", sticky=True)
