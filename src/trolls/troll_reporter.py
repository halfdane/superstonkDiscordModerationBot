from reddit_item_handler import Handler


class TrollReporter(Handler):

    def __init__(self, readonly_reddit, superstonk_subreddit, troll_repository, send_discord_message, **_):
        super().__init__()
        self.readonly_reddit = readonly_reddit
        self.superstonk_subreddit = superstonk_subreddit
        self.troll_repository = troll_repository
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "report potential trolls when they get active in superstonk"

    async def take(self, item):
        troll_source = await self.troll_repository.get_troll_source(item)
        if troll_source is not None:
            await item.report(f"Potential Troll: user has posted or commented in {troll_source}")
            await self.send_discord_message(item=item, description_beginning=f"Potential Troll from {troll_source}")





