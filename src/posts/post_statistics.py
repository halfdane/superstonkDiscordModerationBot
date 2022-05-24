import logging


class CalculatePostStatistics:

    def __init__(self, post_repo=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.persist_posts = post_repo

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Scheduling statistics calculation")
        scheduler.add_job(self.update_posts, "cron", hour="*")
        scheduler.add_job(self.calculate_statistics, "cron", hour="00", minute="05")

    async def update_posts(self):
        self._logger.info(f"Starting to update posts database")
        self._logger.info(f"Fetching top 100 posts")
        self._logger.info(f"Storing updated info for top 100 posts")

    async def calculate_statistics(self):
        self._logger.info(f"calculating interesting stats from the last 24 hours")



