import re

from reddit_item_handler import Handler

IGNORE_BOTS = [
    "Automoderator",
    "Superstonk_QV",
    "Superstonk-Flairy",
    "Roid_Rage_Smurf"
]


class ModTagger(Handler):

    def __init__(self, readonly_reddit, superstonk_subreddit,
                 send_discord_message, superstonk_moderators, **_):
        super().__init__()
        self.readonly_reddit = readonly_reddit
        self.superstonk_subreddit = superstonk_subreddit
        self.send_discord_message = send_discord_message

        self.mods = [mod.name.lower() for mod in superstonk_moderators if mod not in IGNORE_BOTS]
        underscored = [mod.replace("_", "\_") for mod in self.mods if "_" in mod]
        self.mods.extend(underscored)
        self.mods.append("!mods!")
        self.mods.append("!mods !")
        self.mods.append("! mods!")
        self.mods.append("! mods !")

        self.titlematch_regex = [re.compile(r"\bmods?\b", re.IGNORECASE), re.compile(r"\bmoderators?\b", re.IGNORECASE)]

    def wot_doing(self):
        return f"report content where people try to tag mods {self.mods}"

    async def take(self, item):
        author = getattr(item, 'author', "")
        if author.name == "Roid_Rage_Smurf":
            return

        if hasattr(item, 'title'):
            title = getattr(item, 'title', "")
            for r in self.titlematch_regex:
                if r.search(title) is not None:
                    await self.send_discord_message(channel='mod_tag_channel', item=item,
                                                    description_beginning=f"Mod-Post")
                    return

        body = getattr(item, 'body', "")
        for mod in self.mods:
            if mod in body.lower():
                await self.send_discord_message(channel='mod_tag_channel', item=item,
                                                description_beginning=f"Moderator Tag ({mod})")
                return
