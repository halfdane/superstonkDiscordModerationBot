import datetime
import re

from helper.item_helper import permalink, author
from helper.mod_notes import fetch_modnotes
from reddit_item_handler import Handler

RULE_1 = re.compile(r"rule\s*1", re.IGNORECASE)


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
        mod_report_count = len([r[1] for r in item.mod_reports if r[1] != "AutoModerator"])
        mods_reporting_rule_1 = [r[1] for r in item.mod_reports if RULE_1.search(r[0])]

        lots_of_reports = 10
        if item.__class__.__name__ == "Submission":
            lots_of_reports = 3
        elif item.__class__.__name__ == "Comment":
            lots_of_reports = 2

        if len(mods_reporting_rule_1) > 0:
            await self.__send_ban_list(mods_reporting_rule_1, item)
        elif user_report_count >= lots_of_reports or mod_report_count > 0:
            await item.load()
            self._logger.debug(f"Sending reported item {permalink(item)}")
            await self.send_discord_message(item=item, description_beginning="Report")

    async def __send_ban_list(self, mods_reporting_rule_1, item):
        modnotes = fetch_modnotes(reddit=self.readonly_reddit,
                                  redditor_param=author(item),
                                  only='banuser',
                                  subreddit_name=self.subreddit_name)
        bans = f"All bans of {author(item)}   "
        async for k, v in modnotes:
            bans += f"- **{k}**: {v}   \n"
        bans += "\n\nThat's all"
        utc_datetime = datetime.datetime.utcnow()
        formatted_string = utc_datetime.strftime("%Y-%m-%d-%H%MZ")
        for reporting_mod in mods_reporting_rule_1:
            mod = await self.readonly_reddit.redditor(reporting_mod)

            await mod.message(f"Bans of {author(item)} at {formatted_string}", bans)
