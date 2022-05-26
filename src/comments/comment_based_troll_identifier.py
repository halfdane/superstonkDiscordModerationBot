import logging
from datetime import timedelta, datetime

import disnake

from comments.comment_repository import Comments
from helper.links import permalink


class CommentBasedTrollIdentifier:

    def __init__(self, comment_repo: Comments = None, readonly_reddit=None, report_channel=None, report_comments_channel=None,
                 add_reactions_to_discord_message=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.persist_comments = comment_repo
        self.readonly_reddit = readonly_reddit
        self.report_channel = report_channel
        self.report_comments_channel = report_comments_channel
        self.add_reactions_to_discord_message = add_reactions_to_discord_message

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Ready to identify possible trolls from comments")
        scheduler.add_job(self.update_comments, "cron", minute="*/10")
        scheduler.add_job(self.identify_comment_removers, "cron", minute="1-59/10")
        scheduler.add_job(self.identify_mass_downvoted_authors, "cron", day="*")
        scheduler.add_job(self.identify_heavily_downvoted_comments, "cron", hour="*", next_run_time=datetime.now())

    async def update_comments(self):
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        self._logger.debug(f"Fetching ids of comments from the last hour")
        comment_ids_of_last_hour = [f"t1_{c}" for c in await self.persist_comments.ids(last_hour)]
        self._logger.debug(f"Fetching comment information from the last hour")
        comments_of_last_hour = [c async for c in self.readonly_reddit.info(comment_ids_of_last_hour)]
        self._logger.info(f"Storing updated info for {len(comments_of_last_hour)} comments from the last hour")
        await self.persist_comments.store(comments_of_last_hour)

    async def identify_comment_removers(self):
        self._logger.info(f"checking database for people who have lots of downvoted comments that are then removed")
        now = datetime.utcnow()
        await self.method_name(
            "**Found a possible comment deleting troll**",
            self.persist_comments.find_authors_with_removed_negative_comments(since=now - timedelta(hours=1)))

    async def identify_mass_downvoted_authors(self):
        self._logger.info(f"checking database for people who have lots of downvoted comments")
        now = datetime.utcnow()
        await self.method_name(
            "**Found a possibly mass downvoted troll**",
            self.persist_comments.find_authors_with_negative_comments(limit=-5, since=(now - timedelta(hours=36))))

    async def method_name(self, message, future_from_db):
        authors = dict()
        for author, comment_id, score in await future_from_db:
            comments_of_author = authors.get(author, [])
            comments_of_author.append(comment_id)
            authors[author] = comments_of_author

        sus = {k: v for k, v in authors.items() if len(v) > 3}
        self._logger.debug(f"These are the suspicious ones: {sus}")
        for author, comments in sus.items():
            embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
            embed.description = message
            embed.add_field("Redditor", f"[{author}](https://www.reddit.com/u/{author})", inline=False)

            ids = ",".join([c for c in comments])
            link_to_history = f'https://api.pushshift.io/reddit/search/comment/?ids={ids}&fields=author,body,score,full_link'
            embed.add_field("Comments", f"[{ids}]({link_to_history})", inline=False)

            msg = await self.report_comments_channel.send(embed=embed)
            await self.add_reactions_to_discord_message(msg)

    async def identify_heavily_downvoted_comments(self):
        now = datetime.utcnow()
        since = now - timedelta(hours=1)
        self._logger.info(f"checking database for heavily downvoted comments since {since} ({since.timestamp()})")
        downvoted_ids = await self.persist_comments.heavily_downvoted_comments(since=since, limit=-10)

        downvoted_comments = [c async for c in self.readonly_reddit.info(downvoted_ids)]
        for comment in downvoted_comments:
            author = getattr(comment.author, 'name', str(comment.author))
            embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
            embed.description = "**Found a heavily downvoted comment**"
            embed.add_field("Redditor", f"[{author}](https://www.reddit.com/u/{author})", inline=False)
            embed.add_field("Comment", f"[{comment.body[:50]}]({permalink(comment)})", inline=False)
            embed.add_field("Score", f"{comment.score}", inline=False)

            msg = await self.report_comments_channel.send(embed=embed)
            await self.add_reactions_to_discord_message(msg)

