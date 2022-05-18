import json
import logging
import re
from typing import Optional

import asyncpraw
import disnake
import yaml
from decouple import config
from disnake import Message
from disnake.ext import commands
from disnake.ext.commands import Bot

from cogs.modqueue_cog import ModQueueCog
from cogs.user_cog import UserCog
from discordReaction.delete_reaction import DeleteReaction
from discordReaction.help_reaction import HelpReaction
from discordReaction.modnote_reaction import ModNoteReaction
from discordReaction.user_history_reaction import UserHistoryReaction
from discordReaction.wip_reaction import WipReaction
from discord_output_logger import DiscordOutputLogger
from hanami_mail_responder import Hanami
from helper import reddit_helper
from helper.redditor_extractor import extract_redditor
from persistence.posts import Posts
from redditItemHandler.flairy import Flairy
from redditItemHandler.front_desk_sticky import FrontDeskSticky
from redditItemHandler.important_reports import ImportantReports
from redditItemHandler.post_count_limiter import PostCountLimiter
from redditItemHandler.post_to_db import PostToDbHandler
from streamer.streamer import Stream


class SuperstonkModerationBot(Bot):
    COMPONENTS = dict()

    reddit: asyncpraw.Reddit = None
    flairy_reddit: asyncpraw.Reddit = None
    subreddit: Optional[asyncpraw.reddit.Subreddit] = None
    report_channel = None
    flairy_channel = None
    log_output_channel = None
    moderators = None
    logger = logging.getLogger(__name__)
    automod_rules = []
    GENERIC_REACTIONS = None
    USER_REACTIONS = None
    FLAIR_REACTIONS = None
    ALL_REACTIONS = None

    def __init__(self, reddit, flairy_reddit, qvbot_reddit, **options):
        super().__init__(command_prefix='>',
                         description="Moderation bot for Superstonk.",
                         sync_commands_debug=True,
                         **options)
        self.reddit: asyncpraw.Reddit = reddit
        self.COMPONENTS["readonly_reddit"] = self.reddit

        self.flairy_reddit: asyncpraw.Reddit = flairy_reddit
        self.COMPONENTS["flairy_reddit"] = self.flairy_reddit

        self.COMPONENTS["qvbot_reddit"] = qvbot_reddit

    async def on_ready(self):
        self.subreddit = await self.reddit.subreddit("Superstonk")
        self.COMPONENTS["superstonk_subreddit"] = self.subreddit

        self.COMPONENTS["superstonk_TEST_subreddit"] = await self.reddit.subreddit("testsubsuperstonk")
        self.COMPONENTS["superstonk_moderators"] = [moderator async for moderator in self.subreddit.moderator]

        self.report_channel = self.get_channel(REPORTING_CHANNEL)
        self.COMPONENTS["report_channel"] = self.report_channel

        self.flairy_channel = self.get_channel(FLAIRY_CHANNEL)
        self.COMPONENTS["flairy_channel"] = self.flairy_channel

        self.log_output_channel = self.get_channel(LOG_OUTPUT_CHANNEL)
        self.COMPONENTS["log_output_channel"] = self.log_output_channel

        super().add_cog(UserCog(self, **self.COMPONENTS))
        super().add_cog(ModQueueCog(self, **self.COMPONENTS))

        hanami = Hanami(**self.COMPONENTS)
        await hanami.on_ready()
        super().add_cog(hanami)

        discord_output_logging_handler.on_ready(self.log_output_channel, self.loop)

        self.logger.info(f"{str(bot.user)} with id {str(bot.user.id)} is the discord user")
        self.logger.info(f"{USER_INVESTIGATION_CHANNELS}: discord channel to listen for users")
        self.logger.info(f"{REPORTING_CHANNEL}: discord channel for reports")
        self.logger.info(f"{FLAIRY_CHANNEL}: discord channel for flairy")
        self.logger.info(f"{LOG_OUTPUT_CHANNEL}: discord channel for debugging messages")
        self.logger.info(f"{await self.reddit.user.me()}: listening for reports on reddit")
        self.logger.info(f"{await self.flairy_reddit.user.me()}: handling flair requests on reddit")

        flairy = Flairy(self, **self.COMPONENTS)

        self.GENERIC_REACTIONS = (HelpReaction(self), WipReaction(self), DeleteReaction(self))
        self.USER_REACTIONS = (ModNoteReaction(self), UserHistoryReaction(self))
        self.FLAIR_REACTIONS = (flairy,)

        self.ALL_REACTIONS = self.GENERIC_REACTIONS + self.USER_REACTIONS + self.FLAIR_REACTIONS

        post_repo = Posts()
        await post_repo.on_ready()
        self.COMPONENTS["post_repo"] = post_repo

        Stream("Comments") \
            .from_input(self.subreddit.stream.comments) \
            .with_handlers([flairy]) \
            .start(self.loop)

        Stream("Reports") \
            .from_input(self.subreddit.mod.stream.reports) \
            .with_handlers([ImportantReports(self, **self.COMPONENTS)]) \
            .start(self.loop)

        Stream("Posts") \
            .from_input(self.subreddit.stream.submissions) \
            .with_handlers([PostToDbHandler(self, post_repo), PostCountLimiter(self, **self.COMPONENTS), FrontDeskSticky(self)]) \
            .start(self.loop)

        automod_config = await self.subreddit.wiki.get_page("config/automoderator")
        for rule in automod_config.content_md.split("---"):
            y = yaml.safe_load(rule)
            if y and y.get('action', "") == 'remove':
                self.automod_rules += [re.compile(r) for k, v in y.items() if "regex" in k for r in v]
        self.logger.info(f"Read {len(self.automod_rules)} removal rules from automod rules")

    def is_forbidden_comment_message(self, comment_message):
        return any(rule.search(comment_message) for rule in self.automod_rules)

    async def on_message(self, msg: Message):
        if msg.author.bot or msg.channel.id != USER_INVESTIGATION_CHANNELS:
            return
        if extract_redditor(msg):
            await self.add_reactions(msg, self.USER_REACTIONS)

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
        return message, emoji, member, channel

    async def on_raw_reaction_remove(self, p: disnake.RawReactionActionEvent):
        reaction_information = await self.get_reaction_information(p)
        if reaction_information:
            await self.unhandle_reaction(*reaction_information)

    async def on_raw_reaction_add(self, p: disnake.RawReactionActionEvent):
        reaction_information = await self.get_reaction_information(p)
        if reaction_information:
            await self.handle_reaction(*reaction_information)

    async def add_reactions(self, msg: disnake.Message, reactions=None):
        if reactions is None:
            reactions = self.GENERIC_REACTIONS + self.USER_REACTIONS
        for r in reactions:
            await msg.add_reaction(r.emoji)

    async def handle_reaction(self, message, emoji, user, channel):
        for reaction in self.ALL_REACTIONS:
            if reaction.emoji == emoji:
                await reaction.handle_reaction(message, emoji, user, channel)

    async def unhandle_reaction(self, message, emoji, user, channel):
        for reaction in self.ALL_REACTIONS:
            if reaction.emoji == emoji:
                await reaction.unhandle_reaction(message, emoji, user, channel)


if __name__ == "__main__":
    discord_output_logging_handler = DiscordOutputLogger()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s]: %(message)s',
        handlers=[discord_output_logging_handler, logging.StreamHandler()]
    )

    DISCORD_BOT_TOKEN = config("discord_bot_token")
    REPORTING_CHANNEL = int(config("REPORTING_CHANNEL"))
    FLAIRY_CHANNEL = int(config("FLAIRY_CHANNEL"))
    LOG_OUTPUT_CHANNEL = int(config("LOG_OUTPUT_CHANNEL"))
    USER_INVESTIGATION_CHANNELS = int(config("USER_INVESTIGATION_CHANNELS"))

    GUILD = int(config("GUILD"))

    asyncpraw_reddit = \
        asyncpraw.Reddit(username=(config("reddit_username")), password=(config("reddit_password")),
                         client_id=(config("reddit_client_id")),
                         client_secret=(config("reddit_client_secret")),
                         user_agent="com.halfdane.superstonk_moderation_bot:v0.1.2 (by u/half_dane)")
    flairy_asyncpraw_reddit = \
        asyncpraw.Reddit(username=config("flairy_username"), password=config("flairy_password"),
                         client_id=config("flairy_client_id"),
                         client_secret=config("flairy_client_secret"),
                         user_agent="com.halfdane.superstonk_flairy:v0.2.0 (by u/half_dane)")

    qvbot_asyncpraw_reddit = \
        asyncpraw.Reddit(username=config("qvbot_username"), password=config("qvbot_password"),
                         client_id=config("qvbot_client_id"),
                         client_secret=config("qvbot_client_secret"),
                         user_agent="com.halfdane.superstonk_qvbot:v0.1.0 (by u/half_dane)")

    with asyncpraw_reddit as reddit:
        with flairy_asyncpraw_reddit as flairy_reddit:
            with qvbot_asyncpraw_reddit as qvbot_reddit:
                bot = SuperstonkModerationBot(
                    reddit=reddit,
                    flairy_reddit=flairy_reddit,
                    qvbot_reddit=qvbot_reddit,
                    test_guilds=[GUILD]
                )
                bot.run(DISCORD_BOT_TOKEN)
