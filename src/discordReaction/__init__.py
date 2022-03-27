from discordReaction.delete_reaction import DeleteReaction
from discordReaction.help_reaction import HelpReaction
from discordReaction.modnote_reaction import ModNoteReaction
from discordReaction.user_history_reaction import UserHistoryReaction
from discordReaction.wip_reaction import WipReaction
import disnake

GENERIC_REACTIONS = (WipReaction(), DeleteReaction(), ModNoteReaction(), UserHistoryReaction(), HelpReaction())


async def add_reactions(msg: disnake.Message):
    for r in GENERIC_REACTIONS:
        await msg.add_reaction(r.emoji)


async def handle(message, item, emoji, user, channel, bot: disnake.Client):
    for reaction in GENERIC_REACTIONS:
        if reaction.is_reaction(message, item, emoji, user, channel, bot):
            await reaction.handle(message, item, emoji, user, channel, bot)


async def unhandle(message, item, emoji, user, channel, bot: disnake.Client):
    for reaction in GENERIC_REACTIONS:
        if reaction.is_reaction(message, item, emoji, user, channel, bot):
            await reaction.unhandle(message, item, emoji, user, channel, bot)
