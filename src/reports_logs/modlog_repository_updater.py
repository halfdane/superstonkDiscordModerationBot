import logging
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

from comments.comment_body_repository import CommentBodiesRepository
from comments.comment_repository import Comments


class ModlogRepositoryUpdater:

    def __init__(self, modlog_repo, qvbot_reddit=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.modlog_repo = modlog_repo
        self.qvbot_reddit = qvbot_reddit

    def wot_doing(self):
        return "[internal] and clean up locally stored modlog database"

    async def on_ready(self, scheduler, **kwargs):
        scheduler.add_job(self.cleanup_modlog_repo, "cron", day="1", hour="07")

    async def cleanup_modlog_repo(self):
        this_month = datetime.now()
        this_month = datetime(this_month.year, this_month.month, day=1)
        last_month = this_month - relativedelta(months=1)
        month_before_last = last_month - relativedelta(months=1)

        self._logger.debug(f"deleting modlog entries from the month before the last")
        await self.modlog_repo.remove_before(month_before_last)

