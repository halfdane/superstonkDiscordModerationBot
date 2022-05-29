from disnake import Message

from discordReaction.abstract_reaction import Reaction


def cut(text="", maxlength=None):
    if not text:
        return ''
    if not maxlength or len(text) < maxlength:
        return text
    else:
        return f"{str(text[:maxlength]).strip()}..."


def strikethrough(text, maxlength=None):
    return f"~~{cut(text, maxlength=maxlength)}~~"


def un_strikethrough(text):
    if str(text).startswith("~~") and str(text).endswith("~~"):
        return str(text)[len("~~"):-len("~~")]
    else:
        return text


class WipReaction(Reaction):
    emoji = '✅'

    async def handle_reaction(self, message: Message, user):
        for embed in message.embeds:
            embed.description = strikethrough(embed.description)
            for num, field in enumerate(embed.fields):
                embed.set_field_at(index=num,
                                   name=strikethrough(field.name),
                                   value=strikethrough(field.value),
                                   inline=field.inline)

        await message.edit(embeds=message.embeds)

    async def unhandle_reaction(self, message, user):
        for embed in message.embeds:
            embed.description = un_strikethrough(embed.description)
            for num, field in enumerate(embed.fields):
                embed.set_field_at(index=num,
                                   name=un_strikethrough(field.name),
                                   value=un_strikethrough(field.value),
                                   inline=field.inline)

        await message.edit(embeds=message.embeds)

    @staticmethod
    def description():
        return "Mark the discord message as 'handled' so that it isn't dealt with several times"
