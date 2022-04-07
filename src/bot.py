import asyncio
import json
import logging
import os
import re
import sys

from typing import List, Union

import asyncpraw
import disnake
from disnake import Message
from disnake.ext import commands
from disnake.ext.commands import Bot

import discordReaction
import reddit_helper
import cogs

from helper.redditor_extractor import extract_redditor
from redditItemHandler import Handler
from redditItemHandler.comments_handler import Comments
from redditItemHandler.modmail_handler import ModMail
from redditItemHandler.reports_handler import Reports
from redditItemHandler.submissions_handler import Submissions

logger = logging.getLogger("SuperstonkModerationBot")

REDDIT_CLIENT_SECRET = os.environ["reddit_client_secret"]
REDDIT_CLIENT_ID = os.environ["reddit_client_id"]
REDDIT_PASSWORD = os.environ["reddit_password"]
REDDIT_USERNAME = os.environ["reddit_username"]
TARGET_SUBREDDIT = os.environ['target_subreddit']
DISCORD_BOT_TOKEN = os.environ["discord_bot_token"]
CHANNEL_IDS = [int(channel) for channel in str(os.environ["CHANNEL_IDS"]).split()]
USER_INVESTIGATION_CHANNELS = [int(channel) for channel in str(os.environ["USER_INVESTIGATION_CHANNELS"]).split()]


class SuperstonkModerationBot(Bot):
    def __init__(self, **options):
        super().__init__(command_prefix='>',
                         description="Moderation bot for Superstonk.",
                         test_guilds=[952157731614249040, 828370452132921344],
                         sync_commands_debug=True,
                         **options)
        self.reddit: asyncpraw.Reddit = options.get("reddit")
        self._subreddit: asyncpraw.reddit.Subreddit = None
        self.handlers = None
        self.report_channels = []

    async def on_ready(self):
        self._subreddit = await self.reddit.subreddit(TARGET_SUBREDDIT)
        self.handlers: List[Handler] = [
            # Submissions(),
            # Comments(),
            # ModMail(),
            Reports(self.reddit, self._subreddit)
        ]
        for channel in CHANNEL_IDS:
            self.report_channels.append(self.get_channel(channel))

        for handler in self.handlers:
            self.loop.create_task(handler.start(self.report_channels))
        print(str(bot.user) + ' is running.')

    async def on_message(self, msg: Message):
        if msg.author.bot or msg.channel.id not in USER_INVESTIGATION_CHANNELS:
            return
        if extract_redditor(msg):
            await discordReaction.add_reactions(msg, discordReaction.USER_REACTIONS)

    async def on_command_error(self, ctx: commands.Context, error):
        print(error)

    async def get_item(self, c: Union[str, disnake.Embed]):
        s = str(c) if not isinstance(c, disnake.Embed) else json.dumps(c.to_dict())
        return await reddit_helper.get_item(self.reddit, self._subreddit, s)

    async def get_reaction_information(self, p: disnake.RawReactionActionEvent):
        channel = self.get_channel(p.channel_id)
        if not isinstance(channel, disnake.TextChannel):
            return
        member = p.member
        if getattr(member, "bot", False):
            return

        message: Message = await channel.fetch_message(p.message_id)
        emoji = p.emoji.name if not p.emoji.is_custom_emoji() else "<:{}:{}>".format(p.emoji.name, p.emoji.id)

        item = await self.get_item(message.content) if not message.embeds else await self.get_item(message.embeds[0])

        return message, item, emoji, member, channel, self

    async def on_raw_reaction_remove(self, p: disnake.RawReactionActionEvent):
        reaction_information = await self.get_reaction_information(p)
        if reaction_information:
            await discordReaction.unhandle(*reaction_information)

    async def on_raw_reaction_add(self, p: disnake.RawReactionActionEvent):
        reaction_information = await self.get_reaction_information(p)
        if reaction_information:
            await discordReaction.handle(*reaction_information)


bot = SuperstonkModerationBot(
    reddit=asyncpraw.Reddit(username=REDDIT_USERNAME,
                            password=REDDIT_PASSWORD,
                            client_id=REDDIT_CLIENT_ID,
                            client_secret=REDDIT_CLIENT_SECRET,
                            user_agent="com.halfdane.superstonk_moderation_bot:v0.0.2 (by u/half_dane)"))


from cogs.user_cog import UserCog
from cogs.modqueue_cog import ModQueueCog
bot.add_cog(UserCog(bot))
bot.add_cog(ModQueueCog(bot))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(threadName)s %(message)s')
    bot.run(DISCORD_BOT_TOKEN)
