import re

import asyncpraw
import disnake
from disnake.ext import commands

import discordReaction
from helper.discord_text_formatter import link
from helper.mod_notes import get_mod_notes
from redditItemHandler import Handler


class UserCog(commands.Cog):
    def __init__(self, bot, reddit: asyncpraw.reddit):
        self.reddit = reddit
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'Welcome {member.mention}.')

    @commands.slash_command(
        description="Display some helpful links for the given redditor.",
        options=[disnake.Option(
            name="redditor", description="The redditor you're interested in as `redditor`, `u/redditor` or profile URL"
        )]
    )
    async def user(self, ctx, *, redditor):
        if m := re.match('https://(?:www|old).reddit.com/(?:u|user)/([^/]*)', redditor):
            redditor = m.group(1)
        elif m := re.match(r'u/(.*)', redditor):
            redditor = m.group(1)

        e = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        e.add_field("Redditor", link(f"https://www.reddit.com/u/{redditor}", redditor))

        e.add_field(f"More links:",
                    f"[Camas search for {redditor}]"
                    f"(https://camas.github.io/reddit-search/#%7B%22author%22:%22{redditor}%22,%22subreddit%22:%22Superstonk%22,%22resultSize%22:4500%7D) \n"
                    f"[Modmail for {redditor}](https://mod.reddit.com/mail/search?q={redditor})")

        await ctx.response.send_message(embed=e)
        msg = await ctx.original_message()
        await discordReaction.add_reactions(msg)

