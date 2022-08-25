import logging
from datetime import datetime, timedelta, timezone


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
            print(vars(convo))
            print(vars(conversation))

            highlight = self.is_highlighted(conversation)
            if highlight is not None:
                highlight_date = datetime.fromisoformat(highlight.date)
                if highlight_date > a_minute_ago:
                    await self.send_discord_message(
                        description_beginning='Highlighed modmail',
                        item=convo,
                        tag=1012252468698153022
                    )

    def is_highlighted(self, conversation):
        mod_actions = conversation.mod_actions
        mod_actions.sort(key=lambda c: datetime.fromisoformat(c.date), reverse=True)
        for a in mod_actions:
            if a.action_type_id == 0:
                return a
            elif a.action_type_id == 1:
                return None
        return None

