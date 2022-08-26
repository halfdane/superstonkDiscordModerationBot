from reddit_item_handler import Handler


class ModmailNotification(Handler):

    def __init__(self, send_discord_message, **kwargs):
        super().__init__()
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "Notify on discord when modmails happen"

    async def on_ready(self, **kwargs):
        self._logger.warning(self.wot_doing())

    async def take(self, item):
        self._logger.warning(f"Got a new convo: {vars(item)}")
        await self.send_discord_message(item=item, description_beginning="NEW", channel='report_comments_channel')

