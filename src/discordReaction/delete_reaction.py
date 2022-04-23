import disnake

from discordReaction.abstract_reaction import Reaction


class DeleteReaction(Reaction):
    emoji = '❌'

    async def handle_reaction(self, message, emoji, user, channel):
        await message.delete()

    def description(self):
        return "Remove the discord-message for everyone"
