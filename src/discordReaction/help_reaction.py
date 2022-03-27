from disnake import Message

from bot import SuperstonkModerationBot
from discordReaction.abstract_reaction import Reaction


class HelpReaction(Reaction):
    emoji = '❓'

    async def handle(self, message: Message, item, emoji, user, channel, bot: SuperstonkModerationBot):
        explanations = ["**Generic Reactions**"]
        for reaction in Reaction.__subclasses__():
            r = reaction()
            explanations.append(f"{r.emoji}: {r.description()}")

        explanations.append("")
        explanations.append("**Discord Commands:**")
        for cog in bot.cogs.values():
            for command in cog.get_slash_commands():
                explanations.append(f"/{command.name}: {command.description}")

        await user.send("\n".join(explanations))



    def description(self):
        return "Provide some friendly help texts"
