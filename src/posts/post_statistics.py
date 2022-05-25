import logging
from datetime import datetime, timedelta

import asyncpraw


class CalculatePostStatistics:

    def __init__(self, post_repo=None, superstonk_subreddit=None, comment_repo=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.persist_posts = post_repo
        self.comment_repo = comment_repo
        self.superstonk_subreddit = superstonk_subreddit

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Scheduling statistics calculation")
        scheduler.add_job(self.update_posts("hour"), "cron", hour="*", next_run_time=datetime.now()+timedelta(minutes=1))
        scheduler.add_job(self.update_posts("day"), "cron", day="*", next_run_time=datetime.now())
        # scheduler.add_job(self.calculate_statistics, "cron", hour="00", minute="05")

    def update_posts(self, interval):
        async def update_posts_for_interval():
            self._logger.info(f"Fetch top posts of the last {interval}")
            top_posts = [c async for c in self.superstonk_subreddit.top(interval, limit=25)]
            self._logger.info(f"Storing updated info for top 25 posts")
            await self.persist_posts.store(top_posts)

            all_comments = []
            for submission in top_posts:
                submission.comment_limit = 25
                submission.comment_sort = "top"
                await submission.load()
                comments = submission.comments.list()

                real_comments = [comment for comment in comments if isinstance(comment, asyncpraw.reddit.Comment)]
                all_comments += real_comments

            all_comments.sort(key=lambda comment: comment.score, reverse=True)
            self._logger.info(f"Storing updated info for top 100 posts")
            await self.comment_repo.store(all_comments[:100])
            self._logger.info(f"Done")

        return update_posts_for_interval

    async def calculate_statistics(self):
        self._logger.info(f"calculating interesting stats from the last 24 hours")



