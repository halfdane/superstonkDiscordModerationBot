from datetime import timedelta

from helper.item_helper import permalink, author
from qv_bot.__init import get_qv_comment
from reddit_item_handler import Handler


class RAllStickyCreator(Handler):
    _interval = timedelta(hours=24)

    def __init__(self, qvbot_reddit=None, send_discord_message=None, is_live_environment=None,
                 quality_vote_bot_configuration=None, **kwargs):
        super().__init__()
        self.qvbot_reddit = qvbot_reddit
        self.is_live_environment = is_live_environment
        self.send_discord_message = send_discord_message
        self.quality_vote_bot_configuration = quality_vote_bot_configuration

    def wot_doing(self):
        return "Write a qv comment when a post hits r/all"

    async def take(self, item):
        subreddit = item.subreddit
        if subreddit == "SuperStonk" and (qv_comment := await get_qv_comment(self.qvbot_reddit, item)) is not None:
            is_already_rall_comment = 'r/all' in getattr(qv_comment, 'body', "")
            if is_already_rall_comment:
                return

            await self.send_discord_message(item=item, description_beginning="NEW ON R/ALL")

            if self.is_live_environment:
                self._logger.info(f"adding r/all comment to {permalink(item)}")
                r_all_comment = self.quality_vote_bot_configuration.config['r_all_comment']
                post_from_qbots_view = await self.qvbot_reddit.submission(id=item.id)
                sticky = await post_from_qbots_view.reply(r_all_comment)
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()
            else:
                self._logger.info(f"NOT adding r/all comment to {permalink(item)}")
