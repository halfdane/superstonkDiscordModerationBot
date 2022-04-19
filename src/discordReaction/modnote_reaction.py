import logging

import disnake
from disnake import Message

from superstonkDiscordModerationBot import SuperstonkModerationBot
from discordReaction.abstract_reaction import Reaction
from helper.mod_notes import fetch_modnotes
from helper.redditor_extractor import extract_redditor
from disnake.utils import escape_markdown


class ModNoteReaction(Reaction):
    emoji = '🗒️'

    async def handle(self, message: Message, item, emoji, user, channel, bot: SuperstonkModerationBot):
        redditor = extract_redditor(message)
        try:
            count = 0
            embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
            embed.description = f"**ModNotes for {escape_markdown(redditor)}**\n"
            async for k, v in fetch_modnotes(bot.reddit, redditor):
                count += 1
                embed.add_field(k, v, inline=False)

                if count % 20 == 0:
                    await user.send(embed=embed)
                    embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))

            await user.send(embed=embed)
        except disnake.errors.HTTPException as e:
            self._logger.exception(f"Something went wrong: {e.response}")

    def description(self):
        return "Send the modnotes of the user in the 'Redditor' field via DM"
