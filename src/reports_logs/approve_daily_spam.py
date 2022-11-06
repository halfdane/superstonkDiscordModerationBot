from asyncpraw.const import API_PATH

from helper.item_helper import permalink
from reddit_item_handler import Handler

SPAMMY_REPORT = ['This is spam', 'No FUD, Shills, Bots, Lies, Spam, Phishing']


class ApproveDailySpam(Handler):

    def __init__(self, is_live_environment, send_discord_message, qvbot_reddit, **kwargs):
        super().__init__()
        self.is_live_environment = is_live_environment
        self.send_discord_message = send_discord_message
        self.qvbot_reddit = qvbot_reddit

    def wot_doing(self):
        return "Automatically approve the first 'spam' report from the daily"

    async def take(self, item):
        one_user_report = len(item.user_reports) == 1
        no_mod_report = len(item.mod_reports) == 0
        is_spammy_report = len([r[1] for r in item.user_reports if r[0] in SPAMMY_REPORT]) > 0
        is_in_daily = getattr(item, 'link_title', '').startswith("$GME Daily Directory")

        if one_user_report and no_mod_report and is_spammy_report and is_in_daily:
            self._logger.debug(f"Sending reported item {permalink(item)}")
            if self.is_live_environment:
                await item.mod.approve()

                await self.qvbot_reddit.post(
                    API_PATH["report"],
                    data={"thing_id": item.fullname,
                          "api_type": "json",
                          "from_help_desk": "true",
                          "reason": "site_reason_selected",
                          "site_reason": "It's abusing the report button",
                          "custom_text": "The abuse of the report button was automatically performed "
                                         "on behalf of the r/Superstonk moderation team.\n  "
                                         "Please don't hesitate to reach out for further information."})
