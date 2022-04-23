from disnake import Message

from discordReaction.abstract_reaction import Reaction
from helper.discord_text_formatter import strikethrough, un_strikethrough


class WipReaction(Reaction):
    emoji = '✅'

    async def handle(self, message: Message, item, emoji, user, channel, bot):
        for embed in message.embeds:
            lines = embed.description.split("\n")
            embed.description = "\n".join([strikethrough(line) for line in lines])
            for num, field in enumerate(embed.fields):
                embed.set_field_at(index=num,
                                   name=strikethrough(field.name),
                                   value=strikethrough(field.value),
                                   inline=field.inline)

        await message.edit(embeds=message.embeds)

    async def unhandle(self, message, item, emoji, user, channel, bot):
        for embed in message.embeds:
            lines = embed.description.split("\n")
            embed.description = "\n".join([un_strikethrough(line) for line in lines])
            for num, field in enumerate(embed.fields):
                embed.set_field_at(index=num,
                                   name=un_strikethrough(field.name),
                                   value=un_strikethrough(field.value),
                                   inline=field.inline)

        await message.edit(embeds=message.embeds)

    def description(self):
        return "Mark the discord message as 'handled' so that it isn't dealt with several times"
