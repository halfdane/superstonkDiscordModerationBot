import datetime

from helper.item_helper import permalink, author
from helper.mod_notes import fetch_modnotes
from reddit_item_handler import Handler


class IgnoreReportsOnApprovedContent(Handler):

    def __init__(self, is_live_environment, send_discord_message, qvbot_reddit, **kwargs):
        super().__init__()
        self.is_live_environment = is_live_environment
        self.send_discord_message = send_discord_message
        self.qvbot_reddit = qvbot_reddit

    def wot_doing(self):
        return "Automatically ignore stuff that was approved"

    async def take(self, item):
        one_user_report = len(item.user_reports) == 1
        no_mod_report = len(item.mod_reports) == 0
        is_spammy_report = len([r[1] for r in item.user_reports if r[0] in SPAMMY_REPORT]) > 0
        is_in_daily = getattr(item, 'link_title', '').startswith("$GME Daily Directory")

        if one_user_report and no_mod_report and is_spammy_report and is_in_daily:
            self._logger.debug(f"Sending reported item {permalink(item)}")
            if self.is_live_environment:
                await item.mod.approve()
