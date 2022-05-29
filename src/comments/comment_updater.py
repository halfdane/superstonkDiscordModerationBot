import logging
from datetime import timedelta, datetime

import disnake

from comments.comment_repository import Comments
from helper.links import permalink


class CommentUpdater:

    def __init__(self, comment_repo: Comments = None, readonly_reddit=None, report_channel=None, report_comments_channel=None,
                 add_reactions_to_discord_message=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.persist_comments = comment_repo
        self.readonly_reddit = readonly_reddit
        self.report_channel = report_channel
        self.report_comments_channel = report_comments_channel
        self.add_reactions_to_discord_message = add_reactions_to_discord_message

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Ready to update comments")
        scheduler.add_job(self.update_comments, "cron", minute="*/10")

    async def update_comments(self):
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        self._logger.debug(f"Fetching ids of comments from the last hour")
        comment_ids_of_last_hour = [f"t1_{c}" for c in await self.persist_comments.ids(last_hour)]
        self._logger.debug(f"Fetching comment information from the last hour")
        comments_of_last_hour = [c async for c in self.readonly_reddit.info(comment_ids_of_last_hour)]
        self._logger.info(f"Storing updated info for {len(comments_of_last_hour)} comments from the last hour")
        await self.persist_comments.store(comments_of_last_hour)
