import logging
from datetime import timedelta, datetime
import disnake
from disnake import Message
from disnake.utils import escape_markdown

from persistence.comments import Comments


class FindCommentRemovers:

    def __init__(self, comment_repo: Comments = None, readonly_reddit=None, report_channel=None,
                 add_reactions_to_discord_message=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.persist_comments = comment_repo
        self.readonly_reddit = readonly_reddit
        self.report_channel = report_channel
        self.add_reactions_to_discord_message = add_reactions_to_discord_message

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Ready to identify comment removing trolls")
        scheduler.add_job(self.update_comments, "cron", minute="*/10")
        scheduler.add_job(self.identify_comment_removers, "cron", minute="1-59/10")

    async def update_comments(self):
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        self._logger.info(f"Fetching ids of comments from the last hour")
        comment_ids_of_last_hour = await self.persist_comments.fullnames(last_hour)
        self._logger.info(f"Fetching comment information from the last hour")
        comments_of_last_hour = [c async for c in self.readonly_reddit.info(comment_ids_of_last_hour)]
        self._logger.info(f"Storing updated info for {len(comments_of_last_hour)} comments from the last hour")
        await self.persist_comments.store(comments_of_last_hour)

    async def identify_comment_removers(self):
        self._logger.info(f"checking database for people who have lots of downvoted comments that are then removed")
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        authors = dict()
        for author, comment_id, score in await self.persist_comments.find_authors_with_removed_negative_comments(since=last_hour):
            comments_of_author = authors.get(author, [])
            comments_of_author.append(comment_id)
            authors[author] = comments_of_author

        self._logger.info(f"Authors with at least one negative comment that was deleted: {authors}")
        sus = {k: v for k, v in authors.items() if len(v) > 3}
        self._logger.info(f"These are the suspicious ones: {sus}")

        for author, deleted in sus.items():
            embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
            embed.description = f"**Found a possible comment deleting troll: {author}**  \n"
            embed.add_field("Redditor", f"[{author}](https://www.reddit.com/u/{author})", inline=False)
            embed.add_field("Negative comments that were deleted", deleted, inline=False)

            msg = await self.report_channel.send(embed=embed)
            await self.add_reactions_to_discord_message(msg)
