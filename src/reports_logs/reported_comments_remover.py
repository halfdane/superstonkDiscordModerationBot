import logging

from helper.links import permalink


class ReportedCommentsRemover:

    def __init__(self, superstonk_subreddit, qvbot_reddit, send_discord_message, is_live_environment, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.superstonk_subreddit = superstonk_subreddit
        self.qvbot_reddit = qvbot_reddit
        self.send_discord_message = send_discord_message
        self.is_live_environment = is_live_environment

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
            comments = [c for c in post.comments if
                        len(getattr(c, 'user_reports', [])) > 0 or len(getattr(c, 'mod_reports', [])) > 0]

            for comment in comments:
                if self.is_live_environment:
                    item_from_qvbot_view = await self.qvbot_reddit.submission(comment.id, fetch=False)
                    await item_from_qvbot_view.mod.remove(spam=False, mod_note="Cleaning up")
                else:
                    self._logger.info("Feature isn't active, so I'm not removing anything.")

            if len(comments) > 0:
                await self.send_discord_message(
                    description_beginning="CLEANED UP comments from moderated post",
                    fields={'comments': [permalink(c) for c in comments]})

