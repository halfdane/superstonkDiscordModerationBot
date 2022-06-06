import logging
import random
import re
from datetime import datetime, timedelta

import disnake

from discordReaction.wip_reaction import WipReaction
from helper.links import permalink, make_safe
from redditItemHandler import Handler


class FlairyReport(Handler):
    def __init__(self, flairy_reddit=None,
                 add_reactions_to_discord_message=None,
                 report_channel=None, comment_repo=None, **kwargs):
        Handler.__init__(self)

        self.flairy_reddit = flairy_reddit

        self.report_channel = report_channel
        self.comment_repo = comment_repo
        self.add_reactions_to_discord_message = add_reactions_to_discord_message

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info("Scheduling flairy reports")
        scheduler.add_job(self.report_flairs, "cron", day="*", next_run_time=datetime.now())

    async def report_flairs(self):
        self._logger.info("Running flairy report")
        yesterday = datetime.now() - timedelta(hours=24)
        message = f"Comments the flairy reacted to since {yesterday}:  \n"
        flairy_username = await self.flairy_reddit.user.me()
        comments = await self.comment_repo.fetch(since=yesterday, author=flairy_username)
        c_fids = [f"t1_{c.id}" for c in comments]

        async for comment in self.flairy_reddit.info(c_fids):
            comment_parent = await comment.parent()
            await comment_parent.load()
            message += f"\n- [{comment_parent.author}: {make_safe(comment_parent.body)}]({permalink(comment_parent)})"
            if len(message) > 3000:
                e = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255), description=message)
                m = await self.report_channel.send(embed=e)
                await self.add_reactions_to_discord_message(m)
                message = f"**MORE** comments the flairy reacted to since {yesterday}:  \n"

        if len(message) > 0:
            e = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255), description=message)
            message = await self.report_channel.send(embed=e)
            await self.add_reactions_to_discord_message(message)

