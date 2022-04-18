import asyncio
import json
import json
import logging
import os
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

REDDIT_CLIENT_SECRET = os.environ["reddit_client_secret"]
REDDIT_CLIENT_ID = os.environ["reddit_client_id"]
REDDIT_PASSWORD = os.environ["reddit_password"]
REDDIT_USERNAME = os.environ["reddit_username"]
TARGET_SUBREDDIT = os.environ['target_subreddit']
DISCORD_BOT_TOKEN = os.environ["discord_bot_token"]
REPORTING_CHANNEL = int(os.environ["REPORTING_CHANNEL"])
FLAIRY_CHANNEL = int(os.environ["FLAIRY_CHANNEL"])
USER_INVESTIGATION_CHANNELS = [int(channel) for channel in str(os.environ["USER_INVESTIGATION_CHANNELS"]).split()]


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
        self.subreddit = await self.reddit.subreddit(TARGET_SUBREDDIT)
        self.handlers: List[Handler] = [
            Comments(self),
            Reports(self)
        ]
        self.moderators = [moderator async for moderator in self.subreddit.moderator]
        self.report_channel = self.get_channel(REPORTING_CHANNEL)
        self.flairy_channel = self.get_channel(FLAIRY_CHANNEL)

        self.logger.info(f"{str(bot.user)} is listening to {USER_INVESTIGATION_CHANNELS}.")
        self.logger.info(f"{str(bot.user)} is reporting to {REPORTING_CHANNEL}.")
        self.logger.info(f"Flair requests are reported to {FLAIRY_CHANNEL}.")
        self.logger.info(f"{await self.reddit.user.me()} is listening on reddit.")
        self.logger.info(f"{await self.flairy_reddit.user.me()} is handling flair requests")

        for handler in self.handlers:
            self.loop.create_task(handler.start())

    async def on_message(self, msg: Message):
        if msg.author.bot or msg.channel.id not in USER_INVESTIGATION_CHANNELS:
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


bot = SuperstonkModerationBot(
    reddit=asyncpraw.Reddit(
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent="com.halfdane.superstonk_moderation_bot:v0.0.2 (by u/half_dane)"),
    flairy_reddit=asyncpraw.Reddit(
        username=os.environ["flairy_username"],
        password=os.environ["flairy_password"],
        client_id=os.environ["flairy_client_id"],
        client_secret=os.environ["flairy_client_secret"],
        user_agent="desktop:com.halfdane.superstonk_flairy:v0.1.0 (by u/half_dane)")
)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s]: %(message)s')
    bot.run(DISCORD_BOT_TOKEN)
