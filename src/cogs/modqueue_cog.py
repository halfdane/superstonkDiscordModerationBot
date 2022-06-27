import asyncio
from bisect import bisect_left
from datetime import datetime

import disnake
from disnake.ext import commands

from helper.links import permalink


class ModQueueCog(commands.Cog):
    def __init__(self, superstonk_subreddit, send_discord_message, **kwargs):
        self.superstonk_subreddit = superstonk_subreddit
        self.send_discord_message = send_discord_message

    async def fetch_modqueue(self, type):
        modqueue = []
        weights = []
        async for item in self.superstonk_subreddit.mod.modqueue(limit=None, only=type):
            if getattr(item, 'approved', False) or getattr(item, 'removed_by_category', None) is not None:
                continue
            i = bisect_left(weights, item.num_reports)
            weights.insert(i, item.num_reports)
            modqueue.insert(i, item)
        return modqueue

    async def fetch_top_modqueue(self):
        for q in await asyncio.gather(
                self.fetch_modqueue(type="submissions"),
                self.fetch_modqueue(type="comments")):
            for index, item in enumerate(reversed(q)):
                await self.send_discord_message(item=item, description_beginning="Report")
                if index >= 4:
                    break

    @commands.slash_command(
        description="Fetch the top items from the mod queue"
    )
    async def modq(self, ctx):
        await self.send_discord_message(description_beginning="Fetching modqueue!")
        await self.fetch_top_modqueue()
        await self.send_discord_message(description_beginning="Done modqueue!")
