import logging
from datetime import datetime, timedelta

from helper.item_helper import permalink, removed


class ApproveOldModqueueItems:
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

    def __init__(self, subreddit_name, qvbot_reddit, is_live_environment, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.qvbot_reddit = qvbot_reddit
        self.subreddit_name = subreddit_name
        self.is_live_environment = is_live_environment

    def wot_doing(self):
        return "Approve obsolete modqueue items"

    async def on_ready(self, scheduler, **kwargs):
        scheduler.add_job(self.handle_obsolete_modqueue_items, "cron", minute="17", next_run_time=datetime.now())

    async def handle_obsolete_modqueue_items(self):
        subreddit = await self.qvbot_reddit.subreddit(self.subreddit_name)
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        six_days_ago = datetime.utcnow() - timedelta(days=6)

        async for item in subreddit.mod.modqueue(limit=None):
            if getattr(item, 'approved', True) or removed(item):
                continue
            await self.handle_single_modqueue_item(item, three_days_ago, six_days_ago)

    async def handle_single_modqueue_item(self, item, three_days_ago, six_days_ago):
        forces_manual_approval_unless_old = [report[0] for report in item.user_reports if
                                             report[0] not in self.auto_approvable_reports]
        forces_manual_approval_unless_old += [report[0] for report in item.mod_reports if
                                              report[0] not in self.auto_approvable_reports]
        created_utc = datetime.utcfromtimestamp(item.created_utc)
        a_little_old_but_unimportant = created_utc < three_days_ago \
                                       and len(forces_manual_approval_unless_old) == 0 \
                                       and item.num_reports < 3
        pretty_old = created_utc < six_days_ago
        should_approve = a_little_old_but_unimportant or pretty_old

        if should_approve:
            self._logger.warning(f"APPROVING {item.__class__.__name__} "
                                 f"from {created_utc.strftime('%m/%d/%Y, %H:%M:%S')} "
                                 f"with {item.num_reports} reports "
                                 f"(a_little_old_but_unimportant:{a_little_old_but_unimportant}): "
                                 f"(pretty_old:{pretty_old}): "
                                 f"{permalink(item)}")
            if self.is_live_environment:
                await item.mod.approve()
