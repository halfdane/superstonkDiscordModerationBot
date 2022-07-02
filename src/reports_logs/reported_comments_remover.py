import logging

from helper.links import permalink


class ReportedCommentsRemover:

    def __init__(self, superstonk_subreddit, qvbot_reddit, send_discord_message, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_subreddit = superstonk_subreddit
        self.qvbot_reddit = qvbot_reddit
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "Remove reported comments if the post was removed or locked."

    async def on_ready(self, scheduler, **kwargs):
        self._logger.info(f"Scheduling cleanup of handled reports")
        scheduler.add_job(self.remove_sus_comments, "cron", minute="*")

    async def remove_sus_comments(self):
        delete_post_actions = ['spamlink', 'removelink', 'lock']
        handled_post_ids = [log.target_fullname async for log in self.superstonk_subreddit.mod.log(limit=20)
                        if log.action in delete_post_actions]

        async for post in self.qvbot_reddit.info(handled_post_ids):
            await post.load()
            await post.comments.replace_more(limit=None)
            comments = [permalink(c) for c in post.comments if len(getattr(c, 'user_reports', [])) > 0]

            if len(comments) > 0:
                await self.send_discord_message(description_beginning=", ".join(comments))

