from helper.item_helper import permalink
from reddit_item_handler import Handler

class ImportantReports(Handler):

    def __init__(self, readonly_reddit, subreddit_name, send_discord_message, **kwargs):
        super().__init__()
        self.readonly_reddit = readonly_reddit
        self.subreddit_name = subreddit_name
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "Discord notification for posts and comments with reports"

    async def take(self, item):
        await item.load()
        self._logger.info(f"Sending reported item {permalink(item)}")
        await self.send_discord_message(item=item, description_beginning="Report")
