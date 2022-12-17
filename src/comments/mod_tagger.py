from reddit_item_handler import Handler

class ModTagger(Handler):

    def __init__(self, readonly_reddit, superstonk_subreddit, send_discord_message, superstonk_moderators_strict, **_):
        super().__init__()
        self.readonly_reddit = readonly_reddit
        self.superstonk_subreddit = superstonk_subreddit
        self.superstonk_moderators_strict = superstonk_moderators_strict
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "report content where people try to tag mods"

    async def take(self, item):
        body = getattr(item, 'body', "")

        for mod in self.superstonk_moderators_strict:
            if mod.name in body:
                await self.send_discord_message(item=item, description_beginning=f"Moderator Tag")
                break





