import logging

from helper.item_helper import permalink, removed


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
        scheduler.add_job(self.remove_sus_comments, "cron", minute="*")

    async def remove_sus_comments(self):
        delete_post_actions = ['spamlink', 'removelink', 'lock']
        handled_post_ids = [log.target_fullname async for log in self.superstonk_subreddit.mod.log(limit=10)
                        if log.action in delete_post_actions and log.target_fullname.startswith("t3")]
        await self.handle_post_ids(handled_post_ids)

    async def handle_post_ids(self, handled_post_ids):
        async for post in self.qvbot_reddit.info(handled_post_ids):
            await post.load()
            await post.comments.replace_more(limit=None)
            comments = [c for c in post.comments if
                        len(getattr(c, 'user_reports', [])) > 0 or len(getattr(c, 'mod_reports', [])) > 0]

            success = []
            fail = []

            for comment in comments:
                if self.is_live_environment and not removed(comment):
                    item_from_qvbot_view = await self.qvbot_reddit.comment(comment.id, fetch=False)
                    try:
                        await item_from_qvbot_view.mod.remove(
                            spam=False,
                            mod_note="Automatically removing reported comments from moderated posts")
                        success.append(comment)
                    except:
                        fail.append(comment)
                else:
                    self._logger.info("Feature isn't active, so I'm not removing anything.")

            if len(success) > 0 or len(fail) > 0:
                self._logger.info(
                    f"CLEANED UP comments from moderated post: \n"
                    f"removed: {[permalink(c) for c in success]} \n"
                    f"ignored: {[permalink(c) for c in fail]} \n"
                    )

