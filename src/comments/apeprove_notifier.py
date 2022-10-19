import re

from reddit_item_handler import Handler


class ApeproveNotifier(Handler):

    def __init__(self, send_discord_message, **kwargs):
        super().__init__()
        self.send_discord_message = send_discord_message
        regex_flags = re.IGNORECASE | re.MULTILINE | re.DOTALL
        self.detect_approval_request = re.compile(rf".*!\s*apeprove\s*!", regex_flags)

    def wot_doing(self):
        return "Notify mods of approval requests"

    async def take(self, item):
        body = getattr(item, 'body', "")

        if self.detect_approval_request.search(body):
            self._logger.info(f"Got an approval request")
            await self.send_discord_message(item=item, description_beginning="Approval-Request")


