import disnake

from bot import SuperstonkModerationBot


class Reaction:
    emoji = None

    async def handle(self, message, item, emoji, user, channel, bot: SuperstonkModerationBot):
        pass

    async def unhandle(self, message, item, emoji, user, channel, bot: SuperstonkModerationBot):
        pass

    def is_reaction(self, message, item, e, user, channel, bot: SuperstonkModerationBot):
        return e == self.emoji

    def description(self):
        pass
