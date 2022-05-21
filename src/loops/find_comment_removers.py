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
        scheduler.add_job(self.identify_comment_removers, "cron", hour="1-59/10")

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
        for comment in await self.persist_comments.fetch(since=last_hour, deleted_not_removed=True):
            comments_of_author = authors.get(comment.author, [])
            last_timestamp, last_score = comment.score[-1]
            if last_score < 0:
                comments_of_author.append(comment)
            if len(comments_of_author) > 0:
                authors[comment.author] = comments_of_author

        self._logger.info(f"Authors with at least one negative comment that was deleted: {authors}")
        sus = [k for k, v in authors.items() if len(v) > 3]
        self._logger.info(f"These are the suspicious ones: {sus}")

