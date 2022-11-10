from helper.item_helper import permalink
from reddit_item_handler import Handler


class ApproveReportAbuse(Handler):

    def __init__(self, is_live_environment, **kwargs):
        super().__init__()
        self.is_live_environment = is_live_environment

    def wot_doing(self):
        return "Automatically approve report abuse"

    async def take(self, item):
        is_abuse_report = len([r[1] for r in item.mod_reports if r[0] == "It's abusing the report button"]) > 0

        if is_abuse_report:
            self._logger.debug(f"Approving report abuse item {permalink(item)}")
            if self.is_live_environment:
                await item.mod.approve()
                return True

        return False

