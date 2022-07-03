import logging
import re

import asyncpraw
import disnake
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from disnake import Embed, Colour
from disnake import Message
from disnake.ext import commands
from disnake.ext.commands import Bot

from cogs.hanami_mail_responder import Hanami
from cogs.modqueue_cog import ModQueueCog
from cogs.user_cog import UserCog
from comments.comment_based_spam_identifier import CommentBasedSpamIdentifier
from comments.comment_based_troll_identifier import CommentBasedTrollIdentifier
from comments.comment_repository import Comments
from comments.comment_repository_updater import CommentRepositoryUpdater
from comments.flairy import Flairy
from comments.flairy_comment_repository import FlairyComments
from comments.flairy_report import FlairyReport
from comments.front_desk_sticky import FrontDeskSticky
from comments.resticky_qv_bot import RestickyQualityVoteBot
from discordReactionHandlers.delete_reaction import DeleteReaction
from discordReactionHandlers.help_reaction import HelpReaction
from discordReactionHandlers.modnote_reaction import ModNoteReaction
from discordReactionHandlers.user_history_reaction import UserHistoryReaction
from discordReactionHandlers.wip_reaction import WipReaction
from helper.links import permalink, user_page
from helper.moderation_bot_configuration import ModerationBotConfiguration, CONFIG_HOME
from helper.redditor_extractor import extract_redditor
from posts.WeekendRestrictor import WeekendRestrictor
from posts.post_count_limiter import PostCountLimiter
from posts.post_repository import Posts
from posts.post_repository_updater import PostRepositoryUpdater
from posts.post_statistics import CalculatePostStatistics
from posts.post_url_limiter import UrlPostLimiter
from posts.qv_bot import QualityVoteBot
from posts.qv_bot_configuration import QualityVoteBotConfiguration
from posts.r_all_sticky_creator import RAllStickyCreator
from posts.url_post_repository import UrlPosts
from reddit_item_reader import RedditItemReader
from reports_logs.approve_old_modqueue_items import ApproveOldModqueueItems
from reports_logs.important_reports_handler import ImportantReports
from reports_logs.report_repository import Reports
from reports_logs.reported_comments_remover import ReportedCommentsRemover
from reports_logs.trading_halts_reporter import TradingHaltsReporter
from reports_logs.unreport_handled_items import HandledItemsUnreporter


class SuperstonkModerationBot(Bot):
    COMPONENTS = dict()

    logger = logging.getLogger(__name__)
    automod_rules = []

    GENERIC_REACTIONS = None
    USER_REACTIONS = None
    ALL_REACTIONS = None

    def __init__(self, moderation_bot_configuration, **options):
        intents = disnake.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='>',
                         description="Moderation bot for Superstonk.",
                         sync_commands_debug=True,
                         intents=intents,
                         **options)
        self.moderation_bot_configuration = moderation_bot_configuration

    async def component(self, **kwargs):
        for name, component in kwargs.items():
            if component is not None:
                async def no_op(**_): pass

                on_ready = getattr(component, 'on_ready', no_op)
                await on_ready(**self.COMPONENTS)
                self.COMPONENTS[name] = component

    async def on_ready(self):
        self.COMPONENTS['superstonk_discord_moderation_bot'] = self

        self.COMPONENTS["readonly_reddit"] = \
            asyncpraw.Reddit(**self.moderation_bot_configuration.readonly_reddit_settings(),
                             user_agent="com.halfdane.superstonk_moderation_bot:v0.2.0 (by u/half_dane)")
        self.COMPONENTS["flairy_reddit"] = \
            asyncpraw.Reddit(**self.moderation_bot_configuration.flairy_reddit_settings(),
                             user_agent="com.halfdane.superstonk_flairy:v0.2.1 (by u/half_dane)")
        self.COMPONENTS["qvbot_reddit"] = \
            asyncpraw.Reddit(**self.moderation_bot_configuration.qvbot_reddit_settings(),
                             user_agent="com.halfdane.superstonk_qvbot:v0.1.1 (by u/half_dane)")

        self.moderation_bot_configuration.remove_secrets()

        # CONFIGURATION VALUES
        await self.component(**self.moderation_bot_configuration)


        # CHANNELS
        self.logger.warning(f"report into the discord channel: {self.COMPONENTS['report_channel_id']}")
        await self.component(report_channel=self.get_channel(self.COMPONENTS['report_channel_id']))

        self.logger.warning(
            f"use this discord channel for experimental comment stuff: {self.COMPONENTS['report_comments_channel_id']}")
        await self.component(report_comments_channel=self.get_channel(self.COMPONENTS['report_comments_channel_id']))

        self.logger.warning(f"use this discord channel for flairy{self.COMPONENTS['flairy_channel_id']}")
        await self.component(flairy_channel=self.get_channel(self.COMPONENTS['flairy_channel_id']))

        self.logger.warning(f"use this discord channel for debugging messages: {self.COMPONENTS['logging_output_channel_id']}")
        await self.component(logging_output_channel=self.get_channel(self.COMPONENTS['logging_output_channel_id']))

        self.logger.warning(f"listen for user mentions in this discord channel: {self.COMPONENTS['user_investigation_channel_id']}")

        self.logger.warning(f"Read configuration from {CONFIG_HOME}")

        # ALREADY EXISTING OBJECTS
        await self.component(discord_bot_user=self.user)
        self.logger.warning(
            f"use discord user {self.COMPONENTS['discord_bot_user']} with id {self.COMPONENTS['discord_bot_user'].id}")

        self.COMPONENTS["readonly_reddit_username"] = await self.COMPONENTS['readonly_reddit'].user.me()
        self.logger.warning(f"use generic reddit user readonly: {self.COMPONENTS['readonly_reddit_username']}")

        self.COMPONENTS["flairy_reddit_username"] = await self.COMPONENTS['flairy_reddit'].user.me()
        self.logger.warning(f"use this reddit user for flair requests: {self.COMPONENTS['flairy_reddit_username']}")

        self.COMPONENTS["qvbot_reddit_username"] = await self.COMPONENTS['qvbot_reddit'].user.me()
        self.logger.warning(f"use this reddit user for QV bot business: {self.COMPONENTS['qvbot_reddit_username']}")

        await self.component(asyncio_loop=self.loop)

        # FUNCTION COMPONENTS
        await self.component(add_reactions_to_discord_message=self.add_reactions)
        await self.component(get_discord_cogs=lambda: self.cogs)
        await self.component(is_forbidden_comment_message=self.is_forbidden_comment_message)
        await self.component(send_discord_message=self.send_discord_message)

        # FUNDAMENTAL COMPONENTS WITHOUT DEPENDENCIES
        logging.getLogger('apscheduler').setLevel(logging.WARN)

        scheduler_timezone = {}
        scheduler = AsyncIOScheduler(**scheduler_timezone)
        scheduler.start()
        await self.component(scheduler=scheduler)

        subreddit_name_ = self.COMPONENTS["subreddit_name"]
        superstonk_subreddit = await self.COMPONENTS["readonly_reddit"].subreddit(subreddit_name_)
        await self.component(superstonk_subreddit=superstonk_subreddit)
        superstonk_moderators=[m async for m in superstonk_subreddit.moderator]
        await self.component(superstonk_moderators_strict=superstonk_moderators)
        await self.component(superstonk_moderators=superstonk_moderators + ["Roid_Rage_Smurf"])

        self.logger.warning(f"{subreddit_name_} => {superstonk_subreddit}")

        r_all_subreddit = await self.COMPONENTS["readonly_reddit"].subreddit("all")
        await self.component(r_all_subreddit=r_all_subreddit)

        testsubsuperstonk = await self.COMPONENTS["readonly_reddit"].subreddit("testsubsuperstonk")
        await self.component(superstonk_TEST_subreddit=testsubsuperstonk)

        await self.component(quality_vote_bot_configuration=QualityVoteBotConfiguration(**self.COMPONENTS))

        # DATABASE
        await self.component(post_repo=Posts())
        await self.component(url_post_repo=UrlPosts(**self.COMPONENTS))
        await self.component(comment_repo=Comments())
        await self.component(flairy_comment_repo=FlairyComments())
        await self.component(report_repo=Reports())

        # SCHEDULED COMPONENTS
        await self.component(calculate_post_statistics=CalculatePostStatistics(**self.COMPONENTS))
        await self.component(comment_based_troll_identifier=CommentBasedTrollIdentifier(**self.COMPONENTS))
        await self.component(comment_repository_updater=CommentRepositoryUpdater(**self.COMPONENTS))
        await self.component(post_repository_updater=PostRepositoryUpdater(**self.COMPONENTS))
        await self.component(handled_items_unreporter=HandledItemsUnreporter(**self.COMPONENTS))
        await self.component(flairy_report=FlairyReport(**self.COMPONENTS))
        # await self.component(gme_ticker_as_user_name=GmeTickerAsUserName(**self.COMPONENTS))
        await self.component(trading_halts_reporter=TradingHaltsReporter(**self.COMPONENTS))
        await self.component(reported_comments_remover=ReportedCommentsRemover(**self.COMPONENTS))
        await self.component(approve_old_modqueue_items=ApproveOldModqueueItems(**self.COMPONENTS))

        # COGS
        hanami = Hanami(**self.COMPONENTS)
        await self.component(hanami=hanami)
        super().add_cog(hanami)
        super().add_cog(UserCog(**self.COMPONENTS))
        super().add_cog(ModQueueCog(**self.COMPONENTS))

        # REACTIONS
        self.GENERIC_REACTIONS = (
            HelpReaction(**self.COMPONENTS), WipReaction(**self.COMPONENTS), DeleteReaction(**self.COMPONENTS))
        self.USER_REACTIONS = (ModNoteReaction(**self.COMPONENTS), UserHistoryReaction(**self.COMPONENTS))
        self.ALL_REACTIONS = self.GENERIC_REACTIONS + self.USER_REACTIONS

        # STREAMING REDDIT ITEMS INTO HANDLERS
        await self.component(comments_reader=RedditItemReader(
            name="Comments",
            item_fetch_function=superstonk_subreddit.stream.comments,
            item_repository=self.COMPONENTS['comment_repo'],
            handlers=[
                CommentBasedSpamIdentifier(**self.COMPONENTS),
                Flairy(**self.COMPONENTS),
                RestickyQualityVoteBot(**self.COMPONENTS)]))

        await self.component(reports_reader=RedditItemReader(
            name="Reports",
            item_fetch_function=superstonk_subreddit.mod.stream.reports,
            item_repository=self.COMPONENTS['report_repo'],
            handlers=[ImportantReports(**self.COMPONENTS)]))

        await self.component(posts_reader=RedditItemReader(
            name="Posts",
            item_fetch_function=superstonk_subreddit.stream.submissions,
            item_repository=self.COMPONENTS['post_repo'],
            handlers=[
                FrontDeskSticky(),
                PostCountLimiter(**self.COMPONENTS),
                UrlPostLimiter(**self.COMPONENTS),
                WeekendRestrictor(**self.COMPONENTS),
                QualityVoteBot(**self.COMPONENTS),
            ]))

        await self.component(r_all_reader=RedditItemReader(
            name="r/all-Posts",
            item_fetch_function=lambda: r_all_subreddit.hot(limit=50),
            item_repository=None,
            handlers=[RAllStickyCreator(**self.COMPONENTS)]))

        automod_config = await superstonk_subreddit.wiki.get_page("config/automoderator")
        for rule in automod_config.content_md.split("---"):
            y = yaml.safe_load(rule)
            if y and y.get('action', "") == 'remove':
                self.automod_rules += [re.compile(r) for k, v in y.items() if "regex" in k for r in v]
        self.logger.warning(f"Read {len(self.automod_rules)} removal rules from automod rules")
        await self.send_discord_message(description_beginning="Moderation bot restarted")

    def is_forbidden_comment_message(self, comment_message):
        return any(rule.search(comment_message) for rule in self.automod_rules)

    async def on_message(self, msg: Message):
        if msg.author.bot or msg.channel.id != self.COMPONENTS['user_investigation_channel_id']:
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
        return message, emoji, member

    async def on_raw_reaction_remove(self, p: disnake.RawReactionActionEvent):
        reaction_information = await self.get_reaction_information(p)
        if reaction_information:
            await self.unhandle_reaction(*reaction_information)

    async def on_raw_reaction_add(self, p: disnake.RawReactionActionEvent):
        reaction_information = await self.get_reaction_information(p)
        if reaction_information:
            await self.handle_reaction(*reaction_information)

    async def send_discord_message(self,
                                   channel='report_channel',
                                   item=None,
                                   description_beginning='[EMPTY]',
                                   author=None,
                                   fields=None,
                                   **kwargs):
        params = {
            'colour': Colour(0).from_rgb(207, 206, 255),
            'description': description_beginning
        }

        if item:
            params['url'] = permalink(item)
            description = f"{item.__class__.__name__}: {getattr(item, 'title', getattr(item, 'body', ''))[:75]}"
            description = f"**{params['description']}** {description}"
            params['description'] = f"[{description}]({params['url']})"

        e = Embed(**params)

        if author is None:
            author_attr = getattr(item, 'author', None)
            author = getattr(author_attr, 'name', author_attr)
        if author:
            e.add_field("Redditor", f"[{author}]({user_page(author)})", inline=False)

        user_reports_attr = getattr(item, 'user_reports', None)
        if user_reports_attr:
            user_reports = "\n".join(f"{r[1]} {r[0]}" for r in user_reports_attr)
            if user_reports:
                e.add_field("User Reports", user_reports, inline=False)

        mod_reports_attr = getattr(item, 'mod_reports', None)
        if mod_reports_attr:
            mod_reports = "\n".join(f"{r[1]} {r[0]}" for r in mod_reports_attr)
            if mod_reports:
                e.add_field("Mod Reports", mod_reports, inline=False)

        score = getattr(item, 'score', None)
        if score:
            e.add_field("Score:", str(score))

        comments = getattr(item, 'comments', None)
        if comments is not None and len(comments) > 0 and comments[0].author.name == "Superstonk_QV":
            qv_score = str(comments[0].score)
            e.add_field("QV Score:", qv_score)

        upvote_ratio = getattr(item, 'upvote_ratio', None)
        if upvote_ratio:
            e.add_field("Upvote Ratio:", str(upvote_ratio))

        if fields:
            for key, value in fields.items():
                e.add_field(key, value)

        try:
            msg = await self.COMPONENTS[channel].send(embed=e)
            await self.add_reactions(msg)
        except disnake.errors.HTTPException:
            for f in e.fields:
                print(f"{f.name}: {f.value}")
            self.logger.exception("Ignoring this")

    async def add_reactions(self, msg: disnake.Message, reactions=None):
        if reactions is None:
            reactions = self.GENERIC_REACTIONS + self.USER_REACTIONS
        for r in reactions:
            await msg.add_reaction(r.emoji)

    async def handle_reaction(self, message, emoji, user):
        for reaction in self.ALL_REACTIONS:
            if reaction.emoji == emoji:
                await reaction.handle_reaction(message, user)

    async def unhandle_reaction(self, message, emoji, user):
        for reaction in self.ALL_REACTIONS:
            if reaction.emoji == emoji:
                await reaction.unhandle_reaction(message, user)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='[%(name)s]: %(message)s'
    )

    configuration = ModerationBotConfiguration()
    bot = SuperstonkModerationBot(
        moderation_bot_configuration=configuration,
        test_guilds=[configuration['discord_guild_id']]
    )
    bot.run(configuration['discord_bot_token'])
