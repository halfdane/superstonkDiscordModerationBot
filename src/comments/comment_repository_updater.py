import logging
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

from comments.comment_body_repository import CommentBodiesRepository
from comments.comment_repository import Comments


class CommentRepositoryUpdater:

    def __init__(self, comment_repo: Comments = None,
                 comment_body_repo: CommentBodiesRepository = None,
                 readonly_reddit=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.persist_comments = comment_repo
        self.comment_body_repo = comment_body_repo
        self.readonly_reddit = readonly_reddit

    def wot_doing(self):
        return "[internal] Update comments every 10 mins and clean up database"

    async def on_ready(self, scheduler, **kwargs):
        scheduler.add_job(self.update_comments, "cron", minute="*/10")
        scheduler.add_job(self.cleanup_comment_bodies, "cron", day="1", hour="07")

    async def update_comments(self):
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        self._logger.debug(f"Fetching ids of comments from the last hour")
        comment_ids_of_last_hour = [f"t1_{c}" for c in await self.persist_comments.ids(last_hour)]
        self._logger.debug(f"Fetching comment information from the last hour")
        comments_of_last_hour = [c async for c in self.readonly_reddit.info(comment_ids_of_last_hour)]
        self._logger.info(f"Storing updated info for {len(comments_of_last_hour)} comments from the last hour")
        await self.persist_comments.store(comments_of_last_hour)

    async def cleanup_comment_bodies(self):
        this_month = datetime.now()
        this_month = datetime(this_month.year, this_month.month, day=1)
        last_month = this_month - relativedelta(months=1)
        month_before_last = last_month - relativedelta(months=1)

        self._logger.debug(f"Fetching ids of comments from the month before the last")
        comment_ids_of_before_last_month = await self.persist_comments.ids(since=month_before_last, before=last_month)
        self._logger.debug(f"deleting comment bodies from the month before the last")
        await self.comment_body_repo.remove(comment_ids_of_before_last_month)
        self._logger.debug(f"deleting comments from the month before the last")
        await self.persist_comments.remove(comment_ids_of_before_last_month)

