import logging
from datetime import timedelta, datetime

from persistence.comments import Comments


class FindCommentRemovers:

    def __init__(self, comment_repo: Comments = None, readonly_reddit=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.persist_comments = comment_repo
        self.readonly_reddit = readonly_reddit

    async def on_ready(self, scheduler, **kwargs):
        scheduler.add_job(self.update_comments, "cron", minute="*/10")
        scheduler.add_job(self.identify_comment_removers, "cron", hour="*")

    async def update_comments(self):
        self._logger.info(f"Fetching comments from the last hour")
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        self._logger.info(f"Storing updated info for comments from the last hour")

    async def identify_comment_removers(self):
        self._logger.info(f"checking database for people who have lots of downvoted comments that are then removed")
