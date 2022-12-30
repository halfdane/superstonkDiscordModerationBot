from reddit_item_handler import Handler

IGNORE_BOTS = [
    "Automoderator",
    "Superstonk_QV",
    "Superstonk-Flairy"
]


class ModTagger(Handler):

    def __init__(self, readonly_reddit, superstonk_subreddit, 
    send_discord_message, superstonk_moderators_strict, **_):
        super().__init__()
        self.readonly_reddit = readonly_reddit
        self.superstonk_subreddit = superstonk_subreddit
        self.superstonk_moderators_strict = superstonk_moderators_strict
        self.send_discord_message = send_discord_message

        self.mods = [mod.name.lower() for mod in superstonk_moderators_strict if mod not in IGNORE_BOTS]
        underscored = [mod.replace("_", "\_") for mod in self.mods if "_" in mod]
        self.mods.extend(underscored)
        self.mods.append("!mods!")
        self.mods.append("!mods !")
        self.mods.append("! mods!")
        self.mods.append("! mods !")

    def wot_doing(self):
        return f"report content where people try to tag mods {self.mods}"

    async def take(self, item):
        body = getattr(item, 'body', "")

        for mod in self.mods:
            if mod in body.lower():
                await self.send_discord_message(channel='mod_tag_channel', item=item, description_beginning=f"Moderator Tag")
                break





