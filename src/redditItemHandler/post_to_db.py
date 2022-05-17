from persistence.posts import Posts
from redditItemHandler import Handler


class PostToDbHandler(Handler):

    def __init__(self, bot, post_repo=None):
        super().__init__(bot)
        self.persist_posts = post_repo

    async def take(self, post):
        await self.persist_posts.store([post])

