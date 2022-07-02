import disnake

from discord_reaction_handler import Reaction


class DeleteReaction(Reaction):
    emoji = '❌'

    async def handle_reaction(self, message, user):
        try:
            await message.delete()
        except disnake.errors.NotFound:
            self._logger.debug("Message that should be deleted is already gone - works for me.")

    @staticmethod
    def description():
        return "Remove the discord-message for everyone"
