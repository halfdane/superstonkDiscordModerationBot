import datetime

from helper.item_helper import permalink, author
from helper.mod_notes import fetch_modnotes
from reddit_item_handler import Handler

URGENT_REPORT = ['No Harassment, Bullying, Doxing, or Threats', 'Threatening, harassing, or inciting violence',
                 "It's promoting hate based on identity or vulnerability",
                 'It threatens violence or physical harm at someone else',
                 "It's sexual or suggestive content involving minors",
                 'NO BRIGADING'],


class ImportantReports(Handler):

    def __init__(self, readonly_reddit, subreddit_name, send_discord_message, **kwargs):
        super().__init__()
        self.readonly_reddit = readonly_reddit
        self.subreddit_name = subreddit_name
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "Discord notification for posts with more that 3 and comments with more than 2 reports"

    async def take(self, item):
        user_report_count = len(item.user_reports)
        mod_report_count = len(item.mod_reports)
        urgent = [report[0] for report in item.user_reports if report[0] in URGENT_REPORT]

        lots_of_reports = 10
        if item.__class__.__name__ == "Submission":
            lots_of_reports = 10
        elif item.__class__.__name__ == "Comment":
            lots_of_reports = 5

        if user_report_count >= lots_of_reports or mod_report_count > 0 or len(urgent) > 0:
            await item.load()
            self._logger.debug(f"Sending reported item {permalink(item)}")
            await self.send_discord_message(item=item, description_beginning="Report")
