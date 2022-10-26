import datetime

from helper.item_helper import permalink, author
from helper.mod_notes import fetch_modnotes
from reddit_item_handler import Handler


class ImportantReports(Handler):

    def __init__(self, readonly_reddit, subreddit_name, send_discord_message, **kwargs):
        super().__init__()
        self.readonly_reddit = readonly_reddit
        self.subreddit_name = subreddit_name
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "Discord notification for posts with more that 3 and comments with more than 2 reports"

    async def take(self, item):
        user_report_count = sum([r[1] for r in item.user_reports])
        mod_report_count = len([r[1] for r in item.mod_reports])

        lots_of_reports = 10
        if item.__class__.__name__ == "Submission":
            lots_of_reports = 2
        elif item.__class__.__name__ == "Comment":
            lots_of_reports = 2

        if user_report_count >= lots_of_reports or mod_report_count > 0:
            await item.load()
            self._logger.debug(f"Sending reported item {permalink(item)}")
            await self.send_discord_message(item=item, description_beginning="Report")
