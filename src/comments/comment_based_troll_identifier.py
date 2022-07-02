import logging
from datetime import timedelta, datetime

from comments.comment_repository import Comments


class CommentBasedTrollIdentifier:

    def __init__(self, comment_repo: Comments = None, readonly_reddit=None,
                 send_discord_message=None,
                 **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.persist_comments = comment_repo
        self.readonly_reddit = readonly_reddit
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "Identify possible trolls that delete their comments"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.warning(self.wot_doing())
        scheduler.add_job(self.identify_comment_removers, "cron", minute="1-59/10")
        scheduler.add_job(self.identify_heavily_downvoted_comments, "cron", hour="*", next_run_time=datetime.now())

    async def identify_comment_removers(self):
        self._logger.info(f"checking database for people who have lots of downvoted comments that are then removed")
        now = datetime.utcnow()

        authors = dict()
        future_from_db = self.persist_comments.find_authors_with_removed_negative_comments(
            since=now - timedelta(hours=1))
        for author, comment_id, score in await future_from_db:
            comments_of_author = authors.get(author, [])
            comments_of_author.append(comment_id)
            authors[author] = comments_of_author

        sus = {k: v for k, v in authors.items() if len(v) > 3}
        self._logger.debug(f"These are the suspicious ones: {sus}")
        for author, comments in sus.items():
            ids = ",".join([c for c in comments])
            link_to_history = f'https://api.pushshift.io/reddit/search/comment/?ids={ids}&fields=author,body,score,full_link'
            await self.send_discord_message(
                author=author,
                description_beginning="Found a possible comment deleting troll",
                fields={"Comments": f"[{ids}]({link_to_history})"})

    async def identify_heavily_downvoted_comments(self):
        now = datetime.utcnow()
        since = now - timedelta(hours=1)
        self._logger.info(f"checking database for heavily downvoted comments since {since} ({since.timestamp()})")
        downvoted_ids = [f"t1_{c}" for c in
                         await self.persist_comments.heavily_downvoted_comments(since=since, limit=-15)]

        downvoted_comments = [c async for c in self.readonly_reddit.info(downvoted_ids)]
        for comment in downvoted_comments:
            await self.send_discord_message(
                item=comment,
                description_beginning="Heavily downvoted comment",
                channel='report_comments_channel')
