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

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info("Write a qv comment when a post hits r/all")

    async def take(self, item):
        subreddit = item.subreddit
        await item.load()
        if subreddit == "SuperStonk" and (qv_comment := await get_qv_comment(self.qvbot_reddit, item)):
            qv_comment_body = getattr(qv_comment, 'body', "")
            is_already_rall_comment = 'r/all' in qv_comment_body
            if is_already_rall_comment:
                return

            await self.send_discord_message(item=item, description_beginning="NEW ON R/ALL")

            if self.is_live_environment:
                self._logger.info(f"adding r/all comment to {permalink(item)}")
                r_all_comment = self.quality_vote_bot_configuration.config['r_all_comment']

                body = self.quality_vote_bot_configuration.render(r_all_comment, original_comment=qv_comment_body)
                await qv_comment.edit(body)
            else:
                self._logger.info(f"NOT adding r/all comment to {permalink(item)}")
