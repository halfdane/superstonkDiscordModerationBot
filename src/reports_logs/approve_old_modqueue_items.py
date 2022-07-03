import logging
from datetime import datetime, timedelta

from helper.links import permalink, removed


class ApproveOldModqueueItems:

    def __init__(self, subreddit_name, qvbot_reddit, send_discord_message, is_live_environment, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.qvbot_reddit = qvbot_reddit
        self.send_discord_message = send_discord_message
        self.subreddit_name = subreddit_name
        self.is_live_environment = is_live_environment

    def wot_doing(self):
        return "Approve obsolete modqueue items or flag for manual inspection"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.warning(self.wot_doing())
        scheduler.add_job(self.handle_obsolete_modqueue_items, "cron", minute="17", next_run_time=datetime.now())

    async def handle_obsolete_modqueue_items(self):
        subreddit = await self.qvbot_reddit.subreddit(self.subreddit_name)
        auto_approvable_reports = [
            'No FUD, Shills, Bots, Lies, Spam, Phishing',
            'Improper Content',
            'This is spam',
            'This is misinformation',
            'No Self-Monetization',
            'Unsure... But it seems sus',
            'DRS Positions & Buy Orders only, No Gain/Loss Porn',
            'No Mass-Shared Content',
            'Score of stickied comment has dropped below threshold',
            'other',
            'Self-Promotion Abuse'
        ]
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        async for item in subreddit.mod.modqueue(limit=None):
            created_utc = datetime.utcfromtimestamp(item.created_utc)
            if created_utc < three_days_ago:
                forces_manual_approval = [report[0] for report in item.user_reports if
                                          report[0] not in auto_approvable_reports]
                forces_manual_approval += [report[0] for report in item.mod_reports if
                                           report[0] not in auto_approvable_reports]

                if getattr(item, 'approved', True):
                    continue
                elif (len(forces_manual_approval) == 0 and item.num_reports < 3) or removed(item):
                    self._logger.warning(f"APPROVING {item.__class__.__name__} "
                                      f"from {created_utc.strftime('%m/%d/%Y, %H:%M:%S')} "
                                      f"with {item.num_reports} reports: {permalink(item)}")
                    if self.is_live_environment:
                        await item.mod.approve()
                else:
                    self._logger.debug(f"Sending reported item {permalink(item)}")
                    await self.send_discord_message(item=item, description_beginning="OLD Report")

