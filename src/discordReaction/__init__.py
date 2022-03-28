from discordReaction.delete_reaction import DeleteReaction
from discordReaction.help_reaction import HelpReaction
from discordReaction.modnote_reaction import ModNoteReaction
from discordReaction.user_history_reaction import UserHistoryReaction
from discordReaction.wip_reaction import WipReaction
import disnake
from bot import SuperstonkModerationBot


GENERIC_REACTIONS = (HelpReaction(), WipReaction(), DeleteReaction())
USER_REACTIONS = (ModNoteReaction(), UserHistoryReaction())


async def add_reactions(msg: disnake.Message, reactions=GENERIC_REACTIONS + USER_REACTIONS):
    for r in reactions:
        await msg.add_reaction(r.emoji)


async def handle(message, item, emoji, user, channel, bot: SuperstonkModerationBot):
    for reaction in GENERIC_REACTIONS + USER_REACTIONS:
        if reaction.is_reaction(message, item, emoji, user, channel, bot):
            await reaction.handle(message, item, emoji, user, channel, bot)


async def unhandle(message, item, emoji, user, channel, bot: SuperstonkModerationBot):
    for reaction in GENERIC_REACTIONS + USER_REACTIONS:
        if reaction.is_reaction(message, item, emoji, user, channel, bot):
            await reaction.unhandle(message, item, emoji, user, channel, bot)
