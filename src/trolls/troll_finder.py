from reddit_item_handler import Handler
from reddit_item_reader import RedditItemReader


IGNORE_THESE = [
    'AutoModerator',
    'RemindMeBot'
]


class TrollFinder(Handler):

    def __init__(self, readonly_reddit, superstonk_subreddit, troll_repository, **kwargs):
        super().__init__()
        self.readonly_reddit = readonly_reddit
        self.superstonk_subreddit = superstonk_subreddit
        self.troll_repository = troll_repository

    def wot_doing(self):
        return "store potential trolls in db when they interact in their troll subs"

    async def take(self, item):
        if item.author is not None and item.author.name not in IGNORE_THESE:
            await self.troll_repository.push(item)

    async def register_streams(self, registration_function, subreddit_name):
        troll_subreddit = await self.readonly_reddit.subreddit(subreddit_name)
        post_reader = RedditItemReader(
            name=f"{subreddit_name}_posts",
            item_fetch_function=troll_subreddit.stream.submissions,
            item_repository=None,
            handlers=[self])

        comment_reader = RedditItemReader(
            name=f"{subreddit_name}_comments",
            item_fetch_function=troll_subreddit.stream.comments,
            item_repository=None,
            handlers=[self])

        registration_args = {
            f"{subreddit_name}_post_reader": post_reader,
            f"{subreddit_name}_comment_reader": comment_reader
        }

        await registration_function(**registration_args)


