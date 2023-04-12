from datetime import datetime

from reddit_item_handler import Handler

class AddBanMessageToModnotes(Handler):

    def __init__(self, superstonk_subreddit, is_live_environment, **_):
        super().__init__()
        self.superstonk_subreddit = superstonk_subreddit
        self.is_live_environment = is_live_environment

    def wot_doing(self):
        return "Add a modnote when users are banned"

    async def take(self, modlog):
        if modlog.action in ['banuser']:
            created_utc = datetime.utcfromtimestamp(modlog.created_utc).strftime("%Y/%m/%d %H:%M:%S")
            modnote = f"{created_utc}: {modlog.details} ban"
            if self.is_live_environment:
                self.superstonk_subreddit.mod.notes.create(
                    label="BAN", note=modnote, redditor=modlog.target_author
                )
            else:
                print("Cowardly refusing to add ban message in test environment")
