import logging
from datetime import datetime

from helper.links import permalink


class HandledItemsUnreporter:

    def __init__(self, superstonk_subreddit=None, report_channel=None, discord_bot_user=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_subreddit = superstonk_subreddit
        self.report_channel = report_channel
        self.discord_bot_user = discord_bot_user

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Scheduling cleanup of handled reports")
        scheduler.add_job(self.unreport_items, "cron", minute="*")
        scheduler.add_job(self.remove_handled_items, "cron", day="*", next_run_time=datetime.now())

    async def unreport_items(self):
        unreport_actions = ['spamlink', 'removelink', 'approvelink', 'spamcomment', 'removecomment', 'approvecomment']
        handled_urls = [permalink(log.target_permalink) async for log in self.superstonk_subreddit.mod.log(limit=100)
                        if log.action in unreport_actions]
        async for message in self.report_channel \
                .history(limit=200) \
                .filter(lambda r: len(getattr(r, 'embeds', [])) > 0 and r.embeds[0].url in handled_urls):
            await message.delete()
            self._logger.info(f'removed report for {message.embeds[0].url}')

    async def remove_handled_items(self):
        def __was_confirmed(message):
            bot_message = message.author.id == self.discord_bot_user.id
            additional_reactions = [r.emoji for r in message.reactions if r.count >= 2]
            confirmed = '✅' in additional_reactions
            return bot_message and confirmed

        run_once_more = True
        while run_once_more:
            run_once_more = False
            async for message in self.report_channel \
                    .history(limit=200) \
                    .filter(__was_confirmed):
                await message.delete()
                run_once_more = True
                self._logger.info(f'removed report for {message.embeds[0].url}')

        self._logger.info("Cleaned up channel")




