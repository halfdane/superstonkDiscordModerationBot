from redditItemHandler import Handler


class CommentToDbHandler(Handler):

    def __init__(self, comment_repo=None, **kwargs):
        super().__init__(None)
        self.comment_repo = comment_repo

    async def on_ready(self):
        self._logger.info("Ready to persist comments")

    async def take(self, comment):
        await self.comment_repo.store([comment])

