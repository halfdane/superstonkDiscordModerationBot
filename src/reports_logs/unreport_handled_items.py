import logging
from datetime import datetime

import disnake
from asyncpraw.exceptions import InvalidURL
from asyncprawcore.exceptions import Forbidden

from helper.item_helper import permalink, removed
from modmail.__init import modmail_id_from_url, modmail_state


class HandledItemsUnreporter:

    def __init__(self, superstonk_subreddit, report_channel, discord_bot_user, readonly_reddit, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_subreddit = superstonk_subreddit
        self.report_channel = report_channel
        self.discord_bot_user = discord_bot_user
        self.readonly_reddit = readonly_reddit

    def wot_doing(self):
        return "Clean up discord notifications of handled reports"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.warning(self.wot_doing())
        scheduler.add_job(self.unreport_items, "cron", minute="*")
        scheduler.add_job(self.remove_handled_items, "cron", minute="*", next_run_time=datetime.now())

    async def unreport_items(self):
        unreport_actions = ['spamlink', 'removelink', 'approvelink', 'spamcomment', 'removecomment', 'approvecomment']
        handled_urls = [permalink(log) async for log in self.superstonk_subreddit.mod.log(limit=100)
                        if log.action in unreport_actions]
        async for message in self.report_channel \
                .history(limit=200) \
                .filter(lambda r: len(getattr(r, 'embeds', [])) > 0 and r.embeds[0].url in handled_urls):
            try:
                await message.delete()
            except disnake.errors.NotFound:
                self._logger.debug("Message that should be deleted is already gone - works for me.")

            self._logger.debug(f'removed report for {message.embeds[0].url}')

    async def remove_handled_items(self):
        def __was_confirmed(message):
            bot_message = message.author.id == self.discord_bot_user.id
            additional_reactions = [r.emoji for r in message.reactions if r.count >= 2]
            confirmed = '✅' in additional_reactions
            return bot_message and confirmed

        async def __was_removed(message):
            url = message.embeds[0].url if len(getattr(message, 'embeds', [])) > 0 else None
            was_removed = False
            if url:
                try:
                    comment = await self.readonly_reddit.comment(url=url)
                    was_removed = removed(comment)
                except Exception:
                    try:
                        submission = await self.readonly_reddit.submission(url=url)
                        was_removed = removed(submission)
                    except Exception:
                        try:
                            id_from_url = modmail_id_from_url(url=url)
                            modmail = await self.readonly_reddit.modmail(id_from_url)
                            was_removed = modmail_state(modmail).archived is not None
                        except Exception:
                            pass
            return was_removed

        def __may_be_removed_automatically(message):
            e: disnake.Embed = message.embeds[0] if len(getattr(message, 'embeds', [])) > 0 else None
            if e is None:
                return True
            for field in e.fields:
                if field.name == "auto_clean":
                    return str(field.value) == 'True'
            return True

        removed_count = 1_000
        while removed_count > 0:
            removed_count = 0
            async for message in self.report_channel.history(limit=100):
                if __may_be_removed_automatically(message) and \
                        (__was_confirmed(message) or (await __was_removed(message))):
                    try:
                        await message.delete()
                        removed_count += 1
                    except (disnake.errors.NotFound, disnake.errors.Forbidden):
                        pass
