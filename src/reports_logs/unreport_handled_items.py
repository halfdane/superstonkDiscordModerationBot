import logging

from helper.links import permalink


class HandledItemsUnreporter:

    def __init__(self, superstonk_subreddit=None, report_channel=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_subreddit = superstonk_subreddit
        self.report_channel = report_channel

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Scheduling cleanup of handled reports")
        scheduler.add_job(self.unreport_items, "cron", minute="*")

    async def unreport_items(self):
        unreport_actions = ['spamlink', 'removelink', 'approvelink', 'spamcomment', 'removecomment', 'approvecomment']
        handled_urls = [permalink(log.target_permalink) async for log in self.superstonk_subreddit.mod.log(limit=100)
                        if log.action in unreport_actions]
        async for message in self.report_channel \
                .history(limit=200) \
                .filter(lambda r: len(getattr(r, 'embeds', [])) > 0 and r.embeds[0].url in handled_urls):
            await message.delete()
            self._logger.info(f'removed report for {message.embeds[0].url}')

