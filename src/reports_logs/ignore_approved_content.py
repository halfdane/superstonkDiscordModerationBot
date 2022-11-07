from helper.item_helper import permalink
from reddit_item_handler import Handler


class IgnoreApprovedContent(Handler):

    def __init__(self, modlog_repo, qvbot_reddit, is_live_environment, **kwargs):
        super().__init__()
        self.modlog_repo = modlog_repo
        self.qvbot_reddit = qvbot_reddit
        self.is_live_environment = is_live_environment
        self.qv_user = None

    def wot_doing(self):
        return "Ignore reports on content that was just approved"

    async def on_ready(self, scheduler, **kwargs):
        self.qv_user = await self.qvbot_reddit.user.me()

    async def take(self, modlog):
        if self.qv_user.fullname == f"t2_{modlog.mod_id36}":
            return

        if modlog.action in ['approvelink', 'approvecomment']:
            fullname = modlog.target_fullname
            async for item in self.qvbot_reddit.info([fullname]):
                self._logger.info(f"ignoring reports on {permalink(item)} after approval by {modlog._mod}")
                if self.is_live_environment:
                    await item.mod.approve()
