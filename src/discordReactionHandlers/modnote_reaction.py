import logging
from asyncio import sleep
from datetime import datetime as dt

import disnake
from disnake import Message
from disnake.utils import escape_markdown

from discord_reaction_handler import Reaction
from helper.item_helper import permalink
from helper.redditor_extractor import extract_redditor
from helper.redditor_history import redditor_history


class ModNoteReaction(Reaction):
    emoji = '🗒️'

    def __init__(self, readonly_reddit, is_live_environment, superstonk_subreddit, **_):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.readonly_reddit = readonly_reddit
        self.is_live_environment = is_live_environment
        self.superstonk_subreddit = superstonk_subreddit

    @staticmethod
    def description():
        return "Send the modnotes of the user in the 'Redditor' field via DM"

    def wot_doing(self):
        return f"{self.emoji} on discord messages: {self.description()}"

    async def handle_reaction(self, message: Message, user):
        redditor = extract_redditor(message)
        try:
            modnotes = await self.fetch_modnotes(redditor)
            await self.send_notes(modnotes, "ModNotes", redditor, user)

            bans = [n for n in modnotes if n.action == 'BAN' or n.action == 'banuser']
            if len(bans) > 0:
                await self.send_notes(bans, "BANS", redditor, user)

            history = await redditor_history(await self.readonly_reddit.redditor(redditor))
            embed = self.create_embed(redditor, "History")

            for k, v in history.items():
                embed.add_field(k, v, inline=False)
            await user.send(embed=embed)

        except disnake.errors.HTTPException as e:
            self._logger.exception(f"Something went wrong: {e.response}")

    async def send_notes(self, modnotes, type, redditor, user):
        embed = self.create_embed(redditor, type)
        count = 0
        for n in modnotes:
            count += 1
            embed.add_field(f"**{n.created_at}**",
                            f"{n.moderator} {n.action} "
                            f"{n.details} {n.description} "
                            f"{n.link}", inline=False)

            if count % 20 == 0:
                await user.send(embed=embed)
                embed = self.create_embed(redditor, type, "(continued)")
        if count % 20 != 0:
            await user.send(embed=embed)

    def create_embed(self, redditor, type, append=""):
        embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
        embed.description = f"**{type} for {escape_markdown(redditor)} {append}**\n"
        if not self.is_live_environment:
            embed.description += " [TEST]"
        return embed

    async def fetch_modnotes(self, redditor_param):
        notes = [n async for n in self.superstonk_subreddit.mod.notes.redditors(redditor_param)]
        infos = self.readonly_reddit.info([note.reddit_id for note in notes if note.reddit_id is not None])
        infos = {info.fullname: info async for info in infos}
        result = []
        for n in reversed(notes):
            n.link = ""
            if reddit_item := infos.get(n.reddit_id):
                title = getattr(reddit_item, 'title', getattr(reddit_item, 'body', "")).replace("\n", "<br>")[:75]
                n.link = f"\n[{title}]({permalink(reddit_item)})"
            n.created_at = dt.fromtimestamp(int(n.created_at)).strftime('%Y-%m-%d %H:%M:%S')
            result.append(n)
        return result
