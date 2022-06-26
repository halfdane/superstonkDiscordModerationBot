from datetime import timedelta

from helper.links import permalink
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
        self._logger.info("Writes a qv comment when a post hits r/all")

    async def take(self, item):
        subreddit = item.subreddit
        await item.load()
        if subreddit == "SuperStonk" and await self.__needs_r_all_comment(item):
            await self.send_discord_message(item=item, item_description="NEW ON R/ALL")
            post_from_qbots_view = await self.qvbot_reddit.submission(item.id, fetch=False)

            if self.is_live_environment:
                self._logger.info(f"adding r/all comment to {permalink(item)}")
                r_all_comment = self.quality_vote_bot_configuration.config['r_all_comment']
                sticky = await post_from_qbots_view.reply(r_all_comment)
                await sticky.mod.distinguish(how="yes", sticky=True)
                await sticky.mod.ignore_reports()
            else:
                self._logger.info(f"NOT adding r/all comment to {permalink(item)}")

    async def __needs_r_all_comment(self, submission):
        myself = await self.qvbot_reddit.user.me()
        has_comments = len(submission.comments) > 0

        if has_comments:
            first_comment = submission.comments[0]
            missing_sticky = not first_comment.stickied
            is_qv_sticky = first_comment.author.name == myself.name
            isnot_rall_comment = 'r/all' not in getattr(first_comment, 'body', "")

            return missing_sticky or (is_qv_sticky and isnot_rall_comment)
        else:
            return True
