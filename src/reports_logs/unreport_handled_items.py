import logging
import re
from datetime import datetime
from urllib.parse import urlparse

import asyncpraw.models
import disnake
from disnake import Embed

from helper.item_helper import permalink, removed
from modmail.__init import modmail_state


class HandledItemsUnreporter:

    def __init__(self, readonly_reddit, superstonk_subreddit, report_channel, discord_bot_user, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_subreddit = superstonk_subreddit
        self.report_channel = report_channel
        self.discord_bot_user = discord_bot_user
        self.readonly_reddit = readonly_reddit

    def wot_doing(self):
        return "Clean up discord notifications of handled reports"

    async def on_ready(self, scheduler, **kwargs):
        scheduler.add_job(self.unreport_items, "cron", minute="*")
        scheduler.add_job(self.remove_handled_items, "cron", minute="*/5", next_run_time=datetime.now())

    async def unreport_items(self):
        unreport_actions = ['spamlink', 'removelink', 'approvelink', 'spamcomment', 'removecomment', 'approvecomment']
        handled_urls = [permalink(log) async for log in self.superstonk_subreddit.mod.log(limit=100)
                        if log.action in unreport_actions]
        async for message in self.report_channel \
                .history(limit=200) \
                .filter(lambda r: self.message_url(r) in handled_urls) \
                .filter(lambda r: self.may_be_removed_automatically(r)):
            try:
                await message.delete()
                self._logger.debug(f'removed report for {self.message_url(message)}')
            except disnake.errors.NotFound:
                self._logger.debug("Message that should be deleted is already gone - works for me.")

    async def remove_handled_items(self):
        async for message in self.report_channel \
                .history(limit=100) \
                .filter(lambda r: isinstance(self.message_url(r), str)) \
                .filter(lambda r: self.may_be_removed_automatically(r)):
            try:
                if await self.was_removed(self.message_url(message)):
                    self._logger.debug(f"Removing message with url {self.message_url(message)}")
                    await message.delete()
            except (disnake.errors.NotFound, disnake.errors.Forbidden):
                pass

    def message_url(self, message):
        return message.embeds[0].url if len(getattr(message, 'embeds', [])) > 0 else None

    async def was_removed(self, url):
        item = await self.get_item(url)
        if isinstance(item, asyncpraw.models.Comment) or isinstance(item, asyncpraw.models.Submission):
            return removed(item)
        if isinstance(item, asyncpraw.models.ModmailConversation):
            state = modmail_state(item)
            return state.archived is not None

        return False

    def may_be_removed_automatically(self, message):
        e: disnake.Embed = message.embeds[0] if len(getattr(message, 'embeds', [])) > 0 else None
        if e is None:
            return True
        for field in e.fields:
            if field.name == "auto_clean":
                return str(field.value) == 'True'
        return True

    REDDIT_URL_PATTERN = re.compile(
        r"((https:\/\/)?((new|www|old|np|mod)\.)?(reddit|redd){1}(\.com|\.it){1}([a-zA-Z0-9\/_]+))")
    POST_URL_PATTERN = re.compile(
        r"/r(?:/(?P<subreddit>\w+))/comments(?:/(?P<submission>\w+))(?:/\w+/(?P<comment>\w+))?")
    MODMAIL_URL_PATTERN = re.compile(
        r"https://mod.reddit.com/mail/all/(?P<id>\w+)")

    async def get_item(self, str):
        for u in self.REDDIT_URL_PATTERN.findall(str):
            if self.is_url(u[0]):
                item = await self.get_item_from_url(u[0])
                if item:
                    return item
                else:
                    continue
        return None

    async def get_item_from_url(self, url):
        match = self.MODMAIL_URL_PATTERN.search(url)
        if match:
            try:
                modmail = await self.superstonk_subreddit.modmail(match.group("id"))
                if hasattr(modmail, "subject"):
                    return modmail
            except Exception as e:
                self._logger.error(f"Failed to fetch modmail by ID '{match.group('id')}': {e}")
            return None

        match = self.POST_URL_PATTERN.search(url)
        if match and not match.group("comment"):
            try:
                return await self.readonly_reddit.submission(match.group("submission"))
            except Exception as e:
                self._logger.error(f"Failed to fetch submission by ID '{match.group('submission')}': {e}")
                return None
        elif match:
            try:
                return await self.readonly_reddit.comment(match.group("comment"))
            except Exception as e:
                self._logger.error(f"Failed to fetch comment by ID '{match.group('comment')}': {e}")
                return None
        else:
            return None

    def is_url(self, url):
        check = urlparse(url)
        return check.scheme != "" and check.netloc != ""
