from disnake import Message

from discord_reaction_handler import Reaction


def old_reddit(text):
    return text.replace('new.reddit', 'old.reddit')


def new_reddit(text):
    return text.replace('old.reddit', 'new.reddit')


class OldRedditReaction(Reaction):
    emoji = '👴'

    async def handle_reaction(self, message: Message, user):
        for embed in message.embeds:
            embed.description = old_reddit(embed.description)
            for num, field in enumerate(embed.fields):
                embed.set_field_at(index=num,
                                   name=old_reddit(field.name),
                                   value=old_reddit(field.value),
                                   inline=field.inline)

        await message.edit(embeds=message.embeds)

    async def unhandle_reaction(self, message, user):
        for embed in message.embeds:
            embed.description = new_reddit(embed.description)
            for num, field in enumerate(embed.fields):
                embed.set_field_at(index=num,
                                   name=new_reddit(field.name),
                                   value=new_reddit(field.value),
                                   inline=field.inline)

        await message.edit(embeds=message.embeds)

    @staticmethod
    def description():
        return "Change all new.reddit URLs to old.reddit"
