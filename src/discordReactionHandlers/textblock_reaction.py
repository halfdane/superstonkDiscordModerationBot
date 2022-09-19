import disnake
from disnake import Message

from discord_reaction_handler import Reaction


class TextblockReaction(Reaction):
    emoji = '♻'

    def __init__(self, hanami_configuration, **kwargs):
        super().__init__()
        self.hanami_configuration = hanami_configuration

    async def handle_reaction(self, message: Message, user):
        embeds = [
            disnake.Embed(
                colour=disnake.Colour(0).from_rgb(207, 206, 255),
                title=k,
                description=v)
            for k, v in self.hanami_configuration.config.items()]

        try:
            await user.send(embeds=embeds)
        except disnake.errors.HTTPException as e:
            self._logger.exception(f"Something went wrong: {e.response}")

    def wot_doing(self):
        return f"{self.emoji} on discord messages: {self.description()}"

    @staticmethod
    def description():
        return "Send useful text blocks via DM to copypase"
