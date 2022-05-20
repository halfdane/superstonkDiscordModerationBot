from disnake import Message
from discordReaction.abstract_reaction import Reaction


class HelpReaction(Reaction):
    emoji = '❓'

    def __init__(self, get_discord_cogs, **kwargs):
        super().__init__()
        self.get_discord_cogs = get_discord_cogs

    async def handle_reaction(self, message: Message, emoji, user, channel):
        explanations = ["**Generic Reactions**"]
        for reaction in Reaction.__subclasses__():
            print(reaction)
            explanations.append(f"{reaction.emoji}: {reaction.description()}")

        explanations.append("")
        explanations.append("**Discord Commands:**")
        for cog in self.get_discord_cogs().values():
            for command in cog.get_slash_commands():
                explanations.append(f"/{command.name}: {command.description}")

        await user.send("\n".join(explanations))

    @staticmethod
    def description():
        return "Provide some friendly help texts"
