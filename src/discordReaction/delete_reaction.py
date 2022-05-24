from discordReaction.abstract_reaction import Reaction


class DeleteReaction(Reaction):
    emoji = '❌'

    async def handle_reaction(self, message, user):
        await message.delete()

    @staticmethod
    def description():
        return "Remove the discord-message for everyone"
