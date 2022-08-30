import logging
from datetime import datetime, timedelta, timezone

from modmail.__init import modmail_state


class HighlightMailNotification:
    def __init__(self, superstonk_subreddit, qvbot_reddit, send_discord_message, **kwargs):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_subreddit = superstonk_subreddit
        self.qvbot_reddit = qvbot_reddit
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "Send discord notifications when modmails get highlighted"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.warning(self.wot_doing())
        scheduler.add_job(self.check_recent_mails, "cron", minute="*")

    async def check_recent_mails(self):
        async for convo in self.superstonk_subreddit.modmail.conversations(state="highlighted"):
            now = datetime.now(timezone.utc).astimezone()
            a_minute_ago = now - timedelta(minutes=1)
            conversation = await self.superstonk_subreddit.modmail(convo.id)

            state = modmail_state(conversation)
            if state.highlighted is not None and state.highlighted > a_minute_ago:
                await self.send_discord_message(
                    description_beginning='Highlighed modmail',
                    item=convo,
                    tag=829007443584483368
                )
