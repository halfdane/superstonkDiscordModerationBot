import logging
from datetime import datetime, timedelta

import disnake

from helper.links import permalink, make_safe


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
        scheduler.add_job(self.calculate_statistics, "cron", hour="12", day_of_week="0",
                          next_run_time=datetime.now())

    async def calculate_statistics(self):
        end = datetime.now()
        end = datetime(end.year, end.month, end.day)
        start = end - timedelta(days=7)

        oldest_post = datetime.utcfromtimestamp(await self.persist_posts.oldest())
        oldest_comment = datetime.utcfromtimestamp(await self.comment_repo.oldest())

        result = f"# Superstonk statistics   \n"
        result += f"For the interval between {start} UTC and {end} UTC \n\n"

        if oldest_post > start:
            result += f"\nPosts don't reach back that long ({oldest_post}). Results may be wrong"

        if oldest_comment > start:
            result += f"\nComments don't reach back that long ({oldest_comment}). Results may be wrong"

        post_count = await self.persist_posts.count(since=start, until=end)
        result += f"\n\nPost count: {post_count}"

        comment_count = await self.comment_repo.count(since=start, until=end)
        result += f"\nComment count: {comment_count}"

        p_ids = await self.persist_posts.top(since=start, until=end)
        p_fids = [f"t3_{_id}" for _id in p_ids]
        c_ids = await self.comment_repo.top(since=start, until=end)
        c_fids = [f"t1_{_id}" for _id in c_ids]
        items = {i.id: i async for i in self.readonly_reddit.info(p_fids + c_fids)}

        top_posts = "\n".join(
            [f"- {items[_id].score}: [{make_safe(items[_id].title)}]({permalink(items[_id])})" for _id in
             p_ids])
        result += f"\n\nTop 10 posts:   \n\n"
        result += top_posts

        top_comments = "\n".join(
            [f"- {items[_id].score}: [{make_safe(items[_id].body)}]({permalink(items[_id])})" for _id in
             c_ids])
        result += f"\n\nTop 10 comments:  \n\n"
        result += top_comments

        flairs = await self.persist_posts.flairs(since=start, until=end)
        counted_flairs = sum([cnt for flair, cnt in flairs])
        flairs = "\n".join([f"- **{cnt}**: {flair}" for flair, cnt in flairs])
        result += f"\n\nPost flair distribution (for {counted_flairs} posts)   \n\n"
        result += flairs

        embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        embed.description = result

        await self.report_channel.send(embed=embed)
