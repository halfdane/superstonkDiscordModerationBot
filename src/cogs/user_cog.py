import re

import asyncpraw
import disnake
from disnake.ext import commands

import discordReaction
from helper.discord_text_formatter import link
from helper.mod_notes import get_mod_notes
from helper.redditor_history import redditor_history
from redditItemHandler import Handler


class UserCog(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'Welcome {member.mention}.')

    @commands.slash_command(
        description="Display some helpful links for the given redditor.",
        options=[disnake.Option(
            name="redditor", description="The redditor you're interested in as `redditor`, `u/redditor` or profile URL",
            required=True
        )]
    )
    async def user(self, ctx, *, redditor):
        await ctx.response.defer()

        if m := re.match('https://(?:www|old).reddit.com/(?:u|user)/([^/]*)', redditor):
            redditor = m.group(1)
        elif m := re.match(r'u/(.*)', redditor):
            redditor = m.group(1)

        redditor = await self._bot.reddit.redditor(redditor)
        history = await redditor_history(redditor)

        e = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        for k, v in history.items():
            e.add_field(k, v, inline=False)

        await ctx.edit_original_message(embed=e)

        msg = await ctx.original_message()
        await discordReaction.add_reactions(msg)

