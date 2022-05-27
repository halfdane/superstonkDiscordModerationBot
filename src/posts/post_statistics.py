import logging
from datetime import datetime, timedelta

import asyncpraw
from disnake.utils import escape_markdown
import disnake

from helper.links import permalink


class CalculatePostStatistics:

    def __init__(self, post_repo=None, superstonk_subreddit=None, comment_repo=None, readonly_reddit=None,
                 report_channel=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.persist_posts = post_repo
        self.comment_repo = comment_repo
        self.superstonk_subreddit = superstonk_subreddit
        self.readonly_reddit = readonly_reddit
        self.report_channel = report_channel

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Scheduling statistics calculation")
        scheduler.add_job(self.update_posts("hour"), "cron", hour="*",
                          next_run_time=datetime.now() + timedelta(minutes=1))
        scheduler.add_job(self.update_posts("day"), "cron", day="*", next_run_time=datetime.now())
        # scheduler.add_job(self.calculate_statistics, "cron", day="*", next_run_time=datetime.now())

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
        end = datetime.now()
        end = datetime(end.year, end.month, end.day)
        start = end - timedelta(days=1)

        oldest_post = datetime.utcfromtimestamp(await self.persist_posts.oldest())
        oldest_comment = datetime.utcfromtimestamp(await self.comment_repo.oldest())

        result = f"# Superstonk statistics for the day between {start} and {end} \n\n"

        if oldest_post > start:
            result += "\nPosts don't reach back that long. Results may be wrong"

        if oldest_comment > start:
            result += "\nComments don't reach back that long. Results may be wrong"

        post_count = await self.persist_posts.count(since=start, until=end)
        result += f"\n\nPost count in the last interval: {post_count}"

        comment_count = await self.comment_repo.count(since=start, until=end)
        result += f"\nComment count in the last interval: {comment_count}"

        p_ids = await self.persist_posts.top(since=start, until=end)
        p_fids = [f"t3_{_id}" for _id in p_ids]
        c_ids = await self.comment_repo.top(since=start, until=end)
        c_fids = [f"t1_{_id}" for _id in c_ids]
        items = {i.id: i async for i in self.readonly_reddit.info(p_fids + c_fids)}

        top_posts = "\n".join(
            [f"- {items[_id].score}: [{escape_markdown(items[_id].title[:30])}...]({permalink(items[_id])})" for _id in
             p_ids])
        result += f"\n\nTop 10 posts of the last interval:   \n\n"
        result += top_posts

        top_comments = "\n".join(
            [f"- {items[_id].score}: [{escape_markdown(items[_id].body[:30])}...]({permalink(items[_id])})" for _id in
             c_ids])
        result += f"\n\nTop 10 comments of the last interval:  \n\n"
        result += top_comments

        flairs = await self.persist_posts.flairs(since=start, until=end)
        counted_flairs = sum([cnt for flair, cnt in flairs])
        flairs = "\n".join([f"- **{cnt}**: {flair}" for flair, cnt in flairs])
        result += f"\n\nPost flair distribution in interval ({counted_flairs})   \n\n"
        result += flairs

        embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        embed.description = result

        await self.report_channel.send(embed=embed)
