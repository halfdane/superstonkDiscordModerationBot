import asyncio
import json
import json
import logging
import os
import sys
from typing import List, Optional

import asyncpraw
import disnake
from disnake import Message
from disnake.ext import commands
from disnake.ext.commands import Bot

import discordReaction
import reddit_helper
from cogs.modqueue_cog import ModQueueCog
from cogs.user_cog import UserCog
from helper.redditor_extractor import extract_redditor
from redditItemHandler import Handler
from redditItemHandler.comments_handler import Comments
from redditItemHandler.reports_handler import Reports

import configparser


class SuperstonkModerationBot(Bot):
    def __init__(self, **options):
        super().__init__(command_prefix='>',
                         description="Moderation bot for Superstonk.",
                         test_guilds=[952157731614249040, 828370452132921344],
                         sync_commands_debug=True,
                         **options)
        self.reddit: asyncpraw.Reddit = options.get("reddit")
        self.flairy_reddit: asyncpraw.Reddit = options.get("flairy_reddit")
        self.subreddit: Optional[asyncpraw.reddit.Subreddit] = None
        self.handlers = None
        self.report_channel = 0
        self.flairy_channel = 0
        self.moderators = None
        self.logger = logging.getLogger(self.__class__.__name__)

        super().add_cog(UserCog(self))
        super().add_cog(ModQueueCog(self))

    async def on_ready(self):
        self.subreddit = await self.reddit.subreddit("Superstonk")
        self.handlers: List[Handler] = [
            Comments(self),
            Reports(self)
        ]
        self.moderators = [moderator async for moderator in self.subreddit.moderator]
        self.report_channel = self.get_channel(REPORTING_CHANNEL)
        self.flairy_channel = self.get_channel(FLAIRY_CHANNEL)

        self.logger.info(f"{str(bot.user)} is the discord user")
        self.logger.info(f"{USER_INVESTIGATION_CHANNELS}: discord channel to listen for users")
        self.logger.info(f"{REPORTING_CHANNEL}: discord channel for reports")
        self.logger.info(f"{FLAIRY_CHANNEL}: discord channel for flairy")
        self.logger.info(f"{await self.reddit.user.me()}: listening for reports on reddit")
        self.logger.info(f"{await self.flairy_reddit.user.me()}: handling flair requests on reddit")

        for handler in self.handlers:
            self.loop.create_task(handler.start())

    async def on_message(self, msg: Message):
        if msg.author.bot or msg.channel.id != USER_INVESTIGATION_CHANNELS:
            return
        if extract_redditor(msg):
            await discordReaction.add_reactions(msg, discordReaction.USER_REACTIONS)

    async def on_command_error(self, ctx: commands.Context, error):
        self.logger.exception(error)

    async def get_item(self, m: Message):
        c = m.content if not m.embeds else m.embeds[0]
        s = str(c) if not isinstance(c, disnake.Embed) else json.dumps(c.to_dict())
        return await reddit_helper.get_item(self.reddit, self.subreddit, s)

    async def get_reaction_information(self, p: disnake.RawReactionActionEvent):
        channel = self.get_channel(p.channel_id)
        if not isinstance(channel, disnake.TextChannel):
            return
        member = p.member
        if getattr(member, "bot", False):
            return

        message: Message = await channel.fetch_message(p.message_id)
        emoji = p.emoji.name if not p.emoji.is_custom_emoji() else "<:{}:{}>".format(p.emoji.name, p.emoji.id)
        item = await self.get_item(message)
        return message, item, emoji, member, channel, self

    async def on_raw_reaction_remove(self, p: disnake.RawReactionActionEvent):
        reaction_information = await self.get_reaction_information(p)
        if reaction_information:
            await discordReaction.unhandle(*reaction_information)

    async def on_raw_reaction_add(self, p: disnake.RawReactionActionEvent):
        reaction_information = await self.get_reaction_information(p)
        if reaction_information:
            await discordReaction.handle(*reaction_information)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s]: %(message)s')

    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "config.ini"

    logging.root.warning(f"Reading config from {config_file}")

    config = configparser.ConfigParser()
    config.read(config_file)

    DISCORD_BOT_TOKEN = config["DISCORD"]["discord_bot_token"]
    REPORTING_CHANNEL = int(config["DISCORD"]["REPORTING_CHANNEL"])
    FLAIRY_CHANNEL = int(config["DISCORD"]["FLAIRY_CHANNEL"])
    USER_INVESTIGATION_CHANNELS = int(config["DISCORD"]["USER_INVESTIGATION_CHANNELS"])

    bot = SuperstonkModerationBot(
        reddit=asyncpraw.Reddit(
            username=config["REDDIT_CREDENTIALS"]["reddit_username"],
            password=config["REDDIT_CREDENTIALS"]["reddit_password"],
            client_id=config["REDDIT_CREDENTIALS"]["reddit_client_id"],
            client_secret=config["REDDIT_CREDENTIALS"]["reddit_client_secret"],
            user_agent="com.halfdane.superstonk_moderation_bot:v0.0.2 (by u/half_dane)"),
        flairy_reddit=asyncpraw.Reddit(
            username=config["FLAIRY_CREDENTIALS"]["flairy_username"],
            password=config["FLAIRY_CREDENTIALS"]["flairy_password"],
            client_id=config["FLAIRY_CREDENTIALS"]["flairy_client_id"],
            client_secret=config["FLAIRY_CREDENTIALS"]["flairy_client_secret"],
            user_agent="desktop:com.halfdane.superstonk_flairy:v0.1.1 (by u/half_dane)")
    )

    bot.run(DISCORD_BOT_TOKEN)
