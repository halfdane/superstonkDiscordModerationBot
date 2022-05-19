from redditItemHandler import Handler


class PostToDbHandler(Handler):

    def __init__(self, post_repo=None, **kwargs):
        super().__init__(None)
        self.persist_posts = post_repo

    async def on_ready(self):
        self._logger.info("Ready to persist posts")

    async def take(self, post):
        await self.persist_posts.store([post])

