import logging

import disnake
from disnake import Message

from bot import SuperstonkModerationBot
from discordReaction.abstract_reaction import Reaction
from helper.discord_text_formatter import unlink
from helper.mod_notes import get_mod_notes

logger = logging.getLogger("ModNoteReaction")


class ModNoteReaction(Reaction):
    emoji = '🗒️'

    async def handle(self, message: Message, item, emoji, user, channel, bot: SuperstonkModerationBot):
        redditor = next(filter(lambda f: "Redditor" in f['name'], message.embeds[0]._fields))['value']
        print(f"got {redditor}")
        redditor, _ = unlink(redditor)
        try:
            for embed in await get_mod_notes(bot.reddit, redditor):
                await user.send(embed=embed)
        except disnake.errors.HTTPException as e:
            logger.exception(f"Something went wrong: {e.response}")

    def description(self):
        return "Send the modnotes of the user in the 'Redditor' field via DM"
