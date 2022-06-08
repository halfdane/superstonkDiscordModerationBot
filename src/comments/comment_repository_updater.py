import logging
from datetime import timedelta, datetime

import disnake

from comments.comment_repository import Comments


class CommentRepositoryUpdater:

    def __init__(self, comment_repo: Comments = None, readonly_reddit=None,
                 add_reactions_to_discord_message=None, report_comments_channel=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.persist_comments = comment_repo
        self.readonly_reddit = readonly_reddit
        self.add_reactions_to_discord_message = add_reactions_to_discord_message
        self.report_comments_channel = report_comments_channel

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Ready to update comments")
        scheduler.add_job(self.update_comments, "cron", minute="*/10", next_run_time=datetime.now())

        comment_ids_with_wrong_score = [f"t1_{c}" for c in await self.persist_comments.wrong_score()]
        comments_with_wrong_score = [c async for c in self.readonly_reddit.info(comment_ids_with_wrong_score)]
        await self.persist_comments.store(comments_with_wrong_score)
        self._logger.info(f"Fixed comments with wrong score")


    async def update_comments(self):
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        self._logger.debug(f"Fetching ids of comments from the last hour")
        comment_ids_of_last_hour = [f"t1_{c}" for c in await self.persist_comments.ids(last_hour)]
        self._logger.debug(f"Fetching comment information from the last hour")
        comments_of_last_hour = [c async for c in self.readonly_reddit.info(comment_ids_of_last_hour)]
        self._logger.info(f"Storing updated info for {len(comments_of_last_hour)} comments from the last hour")
        await self.persist_comments.store(comments_of_last_hour)

        avg_score = sum([c.score for c in comments_of_last_hour]) / len([comments_of_last_hour])
        m = f"{len(comments_of_last_hour)} comments \n sum {sum([c.score for c in comments_of_last_hour])} in last hour: {avg_score}"
        message = await self.report_comments_channel.send(embed=(
            disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255), description=m)))
        await self.add_reactions_to_discord_message(message)
