from disnake import Message

from discordReaction.abstract_reaction import Reaction
from helper.discord_text_formatter import cut


class WipReaction(Reaction):
    emoji = '✅'

    def __init__(self, **kwargs):
        super().__init__(None)

    async def handle_reaction(self, message: Message, emoji, user, channel):
        for embed in message.embeds:
            lines = embed.description.split("\n")
            embed.description = "\n".join([self.strikethrough(line) for line in lines])
            for num, field in enumerate(embed.fields):
                embed.set_field_at(index=num,
                                   name=self.strikethrough(field.name),
                                   value=self.strikethrough(field.value),
                                   inline=field.inline)

        await message.edit(embeds=message.embeds)

    async def unhandle_reaction(self, message, emoji, user, channel):
        for embed in message.embeds:
            lines = embed.description.split("\n")
            embed.description = "\n".join([self.un_strikethrough(line) for line in lines])
            for num, field in enumerate(embed.fields):
                embed.set_field_at(index=num,
                                   name=self.un_strikethrough(field.name),
                                   value=self.un_strikethrough(field.value),
                                   inline=field.inline)

        await message.edit(embeds=message.embeds)

    @staticmethod
    def description():
        return "Mark the discord message as 'handled' so that it isn't dealt with several times"

    def strikethrough(self, text, maxlength=None):
        return f"~~{cut(text, maxlength=maxlength)}~~"

    def un_strikethrough(self, text):
        if str(text).startswith("~~") and str(text).endswith("~~"):
            return str(text)[len("~~"):-len("~~")]
        else:
            return text
