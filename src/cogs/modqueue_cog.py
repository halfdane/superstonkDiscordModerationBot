import asyncio
from bisect import bisect_left
from datetime import datetime

import disnake
from disnake.ext import commands

import discordReaction


class ModQueueCog(commands.Cog):
    def __init__(self, discord_bot):
        self._bot = discord_bot

    async def fetch_modqueue(self, type):
        modqueue = []
        weights = []
        async for item in self._bot.subreddit.mod.modqueue(limit=None, only=type):
            if item.num_reports < 3 or \
                    getattr(item, 'approved', False) or \
                    getattr(item, 'removed_by_category', None) is not None:
                continue

            now = datetime.now()
            item.created_utc = datetime.utcfromtimestamp(item.created_utc)
            hours_passed = (now - item.created_utc).total_seconds() / 3600

            if hours_passed > 48:
                continue

            item.weight = (item.num_reports * 2) / hours_passed
            i = bisect_left(weights, item.weight)
            weights.insert(i, item.weight)
            modqueue.insert(i, item)
        return modqueue

    async def fetch_top_modqueue(self):
        result = []
        for q in await asyncio.gather(
                self.fetch_modqueue(type="submissions"),
                self.fetch_modqueue(type="comments")):
            for index, item in enumerate(reversed(q)):
                result.append(
                    f"{item.__class__.__name__} "
                    f"with {item.num_reports} reports: "
                    f"https://www.reddit.com{item.permalink}")
                if index >= 4:
                    break
        return result

    @commands.slash_command(
        description="Fetch the top items from the mod queue"
    )
    async def modq(self, ctx):
        await ctx.response.defer()

        items = await self.fetch_top_modqueue()

        embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        embed.description = "Top items of the modqueue"
        embed.description += "\n".join(items)
        await ctx.edit_original_message(embed=embed)
        msg = await ctx.original_message()
        await discordReaction.add_reactions(msg, discordReaction.GENERIC_REACTIONS)
