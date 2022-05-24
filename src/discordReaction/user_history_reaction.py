import disnake
from disnake import Message

from discordReaction.abstract_reaction import Reaction
from helper.redditor_extractor import extract_redditor
from helper.redditor_history import redditor_history


class UserHistoryReaction(Reaction):
    emoji = '📜'

    def __init__(self, readonly_reddit, **kwargs):
        super().__init__()
        self.readonly_reddit = readonly_reddit

    async def handle_reaction(self, message: Message, user):
        redditor = extract_redditor(message)
        try:
            history = await redditor_history(await self.readonly_reddit.redditor(redditor))
            embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
            for k, v in history.items():
                embed .add_field(k, v, inline=False)
            await user.send(embed=embed)
        except disnake.errors.HTTPException as e:
            self._logger.exception(f"Something went wrong: {e.response}")

    @staticmethod
    def description():
        return "Fetch some statistics from the user's history"
