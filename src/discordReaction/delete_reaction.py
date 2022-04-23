import disnake

from discordReaction.abstract_reaction import Reaction


class DeleteReaction(Reaction):
    emoji = '❌'

    async def handle(self, message, item, emoji, user, channel, bot):
        await message.delete()

    def description(self):
        return "Remove the discord-message for everyone"
