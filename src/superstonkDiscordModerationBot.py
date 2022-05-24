import logging
import re

import asyncpraw
import disnake
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from decouple import config
from disnake import Message
from disnake.ext import commands
from disnake.ext.commands import Bot

from cogs.hanami_mail_responder import Hanami
from cogs.modqueue_cog import ModQueueCog
from cogs.user_cog import UserCog
from comments.comment_based_troll_identifier import CommentBasedTrollIdentifier
from comments.comment_repository import Comments
from comments.flairy import Flairy
from comments.front_desk_sticky import FrontDeskSticky
from discordReaction.delete_reaction import DeleteReaction
from discordReaction.help_reaction import HelpReaction
from discordReaction.modnote_reaction import ModNoteReaction
from discordReaction.user_history_reaction import UserHistoryReaction
from discordReaction.wip_reaction import WipReaction
from discord_output_logger import DiscordOutputLogger
from helper.redditor_extractor import extract_redditor
from posts.post_count_limiter import PostCountLimiter
from posts.post_repository import Posts
from posts.post_statistics import CalculatePostStatistics
from redditItemHandler.reddit_item_reader import RedditItemReader
from reports_logs.important_reports_handler import ImportantReports
from reports_logs.report_repository import Reports


class SuperstonkModerationBot(Bot):
    COMPONENTS = dict()

    logger = logging.getLogger(__name__)
    automod_rules = []

    GENERIC_REACTIONS = None
    USER_REACTIONS = None
    FLAIR_REACTIONS = None
    ALL_REACTIONS = None

    def __init__(self, readonly_reddit, flairy_reddit, qvbot_reddit, **options):
        super().__init__(command_prefix='>',
                         description="Moderation bot for Superstonk.",
                         sync_commands_debug=True,
                         **options)
        self.COMPONENTS["readonly_reddit"] = readonly_reddit
        self.COMPONENTS["flairy_reddit"] = flairy_reddit
        self.COMPONENTS["qvbot_reddit"] = qvbot_reddit

    async def component(self, name, component=None):
        if component is not None:
            async def no_op(**_): pass

            on_ready = getattr(component, 'on_ready', no_op)
            await on_ready(**self.COMPONENTS)
            self.COMPONENTS[name] = component

        return self.COMPONENTS[name]

    async def on_ready(self):
        logging.getLogger('apscheduler').setLevel(logging.WARN)
        scheduler = AsyncIOScheduler()
        scheduler.start()

        await self.component("scheduler", scheduler)

        await self.component("discord_bot_user", self.user)
        self.logger.info(
            f"{self.COMPONENTS['discord_bot_user']} with id {self.COMPONENTS['discord_bot_user'].id} is the discord user")

        self.logger.info(f"{await self.COMPONENTS['readonly_reddit'].user.me()}: listening for reports on reddit")
        self.logger.info(f"{await self.COMPONENTS['flairy_reddit'].user.me()}: handling flair requests on reddit")
        self.logger.info(f"{await self.COMPONENTS['qvbot_reddit'].user.me()}: handling QV bot business on reddit")

        superstonk_subreddit = await self.COMPONENTS["readonly_reddit"].subreddit("Superstonk")
        testsubsuperstonk = await self.COMPONENTS["readonly_reddit"].subreddit("testsubsuperstonk")
        await self.component("superstonk_subreddit", superstonk_subreddit)
        await self.component("superstonk_moderators", [m async for m in superstonk_subreddit.moderator])
        await self.component("superstonk_TEST_subreddit", testsubsuperstonk)

        await self.component("report_channel", self.get_channel(REPORTING_CHANNEL))
        self.logger.info(f"{REPORTING_CHANNEL}: discord channel for reports")

        await self.component("flairy_channel", self.get_channel(FLAIRY_CHANNEL))
        self.logger.info(f"{FLAIRY_CHANNEL}: discord channel for flairy")

        await self.component("logging_output_channel", self.get_channel(LOG_OUTPUT_CHANNEL))
        self.logger.info(f"{LOG_OUTPUT_CHANNEL}: discord channel for debugging messages")

        await self.component("asyncio_loop", self.loop)
        await self.component("add_reactions_to_discord_message", self.add_reactions)
        await self.component("get_discord_cogs", lambda: self.cogs)
        await self.component("is_forbidden_comment_message", self.is_forbidden_comment_message)
        await self.component("discord_bot_user", self.user)
        await self.component("environment", ENVIRONMENT)

        await self.component("post_repo", Posts())
        await self.component("comment_repo", Comments())
        await self.component("report_repo", Reports())
        await self.component("calculate_post_statistics", CalculatePostStatistics(**self.COMPONENTS))
        await self.component("comment_based_troll_identifier", CommentBasedTrollIdentifier(**self.COMPONENTS))

        hanami = Hanami(**self.COMPONENTS)
        await self.component("hanami", hanami)
        super().add_cog(hanami)

        super().add_cog(UserCog(**self.COMPONENTS))
        super().add_cog(ModQueueCog(**self.COMPONENTS))

        await self.component("discord_output_logging_handler", discord_output_logging_handler)

        self.logger.info(f"{USER_INVESTIGATION_CHANNELS}: discord channel to listen for users")

        flairy = Flairy(self, **self.COMPONENTS)

        self.GENERIC_REACTIONS = (
            HelpReaction(**self.COMPONENTS), WipReaction(**self.COMPONENTS), DeleteReaction(**self.COMPONENTS))
        self.USER_REACTIONS = (ModNoteReaction(**self.COMPONENTS), UserHistoryReaction(**self.COMPONENTS))
        self.FLAIR_REACTIONS = (flairy,)

        self.ALL_REACTIONS = self.GENERIC_REACTIONS + self.USER_REACTIONS + self.FLAIR_REACTIONS

        await self.component("comments_reader",
                             RedditItemReader(
                                 name="Comments",
                                 item_fetch_function=superstonk_subreddit.comments,
                                 item_repository=self.COMPONENTS['comment_repo'],
                                 handlers=[flairy]))

        await self.component("reports_reader",
                             RedditItemReader(
                                 name="Reports",
                                 item_fetch_function=superstonk_subreddit.mod.reports,
                                 item_repository=self.COMPONENTS['report_repo'],
                                 handlers=[ImportantReports(**self.COMPONENTS)]))

        await self.component("posts_reader",
                             RedditItemReader(
                                 name="Posts",
                                 item_fetch_function=superstonk_subreddit.new,
                                 item_repository=self.COMPONENTS['post_repo'],
                                 handlers=[PostCountLimiter(**self.COMPONENTS), FrontDeskSticky()]))

        automod_config = await superstonk_subreddit.wiki.get_page("config/automoderator")
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

    ENVIRONMENT = config("environment")

    readonly_asyncpraw_reddit = \
        asyncpraw.Reddit(username=(config("reddit_username")),
                         password=(config("reddit_password")),
                         client_id=(config("reddit_client_id")),
                         client_secret=(config("reddit_client_secret")),
                         user_agent="com.halfdane.superstonk_moderation_bot:v0.1.2 (by u/half_dane)")
    flairy_asyncpraw_reddit = \
        asyncpraw.Reddit(username=config("flairy_username"),
                         password=config("flairy_password"),
                         client_id=config("flairy_client_id"),
                         client_secret=config("flairy_client_secret"),
                         user_agent="com.halfdane.superstonk_flairy:v0.2.0 (by u/half_dane)")

    qvbot_asyncpraw_reddit = \
        asyncpraw.Reddit(username=config("qvbot_username"),
                         password=config("qvbot_password"),
                         client_id=config("qvbot_client_id"),
                         client_secret=config("qvbot_client_secret"),
                         user_agent="com.halfdane.superstonk_qvbot:v0.1.0 (by u/half_dane)")

    with readonly_asyncpraw_reddit as readonly_reddit:
        with flairy_asyncpraw_reddit as flairy_reddit:
            with qvbot_asyncpraw_reddit as qvbot_reddit:
                bot = SuperstonkModerationBot(
                    readonly_reddit=readonly_reddit,
                    flairy_reddit=flairy_reddit,
                    qvbot_reddit=qvbot_reddit,
                    test_guilds=[GUILD]
                )
                bot.run(DISCORD_BOT_TOKEN)
