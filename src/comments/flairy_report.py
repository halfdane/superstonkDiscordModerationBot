import logging
from datetime import datetime, timedelta

from helper.item_helper import permalink, make_safe, user_page


class FlairyReport:
    def __init__(self, flairy_reddit, send_discord_message,
                 comment_repo, flairy_comment_repo, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.flairy_reddit = flairy_reddit
        self.comment_repo = comment_repo
        self.flairy_comment_repo = flairy_comment_repo
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "Create daily flair reports"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.warning(self.wot_doing())
        scheduler.add_job(self.report_flairs, "cron", day="*")

    async def report_flairs(self):
        self._logger.info("Running flairy report")

        yesterday = datetime.now() - timedelta(hours=24)
        message = f"Comments the flairy reacted to since {yesterday}:  \n"
        flairy_username = await self.flairy_reddit.user.me()
        comments = await self.comment_repo.fetch(since=yesterday, author=flairy_username)

        if len(comments) == 0:
            return

        c_fids = [f"t1_{c.id}" for c in comments]

        async for comment in self.flairy_reddit.info(c_fids):
            comment_parent = await comment.parent()
            await comment_parent.load()
            body = await self.flairy_comment_repo.pop_body(comment_parent.id)
            if body is None:
                self._logger.info(f"no body stored for {comment_parent.id}? using it from reddit instead")
                body = comment_parent.body
            comment_parent_from_own_db = await self.comment_repo.fetch(id=comment_parent.id)

            author_name = comment_parent_from_own_db[0].author.name
            message += f"\n- [{author_name}]({user_page(author_name)}): [{make_safe(body)}]({permalink(comment_parent)})"
            if len(message) > 3000:
                await self.send_discord_message(description_beginning=message)
                message = f"MORE comments the flairy reacted to since {yesterday}:  \n"

        if len(message) > 0:
            await self.send_discord_message(description_beginning=message)
