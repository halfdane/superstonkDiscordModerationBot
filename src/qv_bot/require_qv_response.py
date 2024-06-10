import logging
from datetime import datetime, timedelta, UTC

from helper.item_helper import author, removed, permalink
from qv_bot.__init import get_qv_comment
from reddit_item_handler import Handler


class RequireQvResponse(Handler):
    def __init__(self, qvbot_reddit, post_repo, quality_vote_bot_configuration, automod_configuration,
                 send_discord_message, **kwargs):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.qvbot_reddit = qvbot_reddit
        self.post_repo = post_repo
        self.quality_vote_bot_configuration = quality_vote_bot_configuration
        self.automod_configuration = automod_configuration
        self.send_discord_message = send_discord_message

    def wot_doing(self):
        return "Remove post if QVbot didn't get a response in the allotted time - replaces 'op_response' in template"

    async def on_ready(self, scheduler, **kwargs):
        scheduler.add_job(self.check_recent_comments, "cron", minute="*")

    async def check_recent_comments(self, ):
        now = datetime.now(UTC)
        interval = now - timedelta(minutes=20)
        latest = now - timedelta(minutes=10)

        posts = await self.post_repo.fetch(since=interval)
        p_fids = [f"t3_{c.id}" for c in posts]

        async for post in self.qvbot_reddit.info(p_fids):
            await post.load()
            try:
                await self.inspect_individual_post(post, latest)
            except Exception:
                self._logger.exception("something went wrong")

    async def inspect_individual_post(self, post, latest):
        flair_id = getattr(post, 'link_flair_template_id', 'NONE')
        op_required_comment_key = 'op_required_response_comment_' + flair_id
        op_required_comment = self.quality_vote_bot_configuration.config.get(op_required_comment_key, None)

        post_requires_response = op_required_comment is not None and not removed(post)
        if post_requires_response:
            self._logger.debug(f"Post requires a response: {permalink(post)}")
            qv_comment = await get_qv_comment(self.qvbot_reddit, post)
            if qv_comment is None:
                return

            latest_op_response = await self.get_latest_op_response(qv_comment, post)
            if latest_op_response is not None:
                user_provided_string = latest_op_response.body
                self._logger.debug(f"Got a response from Op: {user_provided_string}")
                if self.automod_configuration.is_forbidden_user_message(user_provided_string):
                    await latest_op_response.report(
                        f"Cowardly refusing to use prohibited user input: {user_provided_string[:50]}")
                else:
                    # use body of response and put it into the qv_body
                    body = self.quality_vote_bot_configuration.render(op_required_comment,
                                                                      op_response=user_provided_string)
                    await qv_comment.edit(body)
            else:
                # if now is over: report or remove post
                created_utc = datetime.utcfromtimestamp(post.created_utc)

                if latest > created_utc:
                    await post.mod.remove(
                        spam=False,
                        mod_note="Automatically removing after timeout without response",
                    )
                    removal_append = \
                        self.quality_vote_bot_configuration.config.get("required_response_missing_comment")
                    body = self.quality_vote_bot_configuration.render(removal_append, original_comment=qv_comment.body)
                    await qv_comment.edit(body)
        else:
            self._logger.debug(f"Post with {flair_id} doesn't require a response")

    async def get_latest_op_response(self, qv_comment, post):
        author_name = author(post)
        comments = qv_comment.replies
        await comments.replace_more(limit=None)
        all_replies = comments.list()
        if len(all_replies) > 0:
            op_responses = [c for c in all_replies if author_name == author(c)]
            op_responses.sort(key=lambda c: c.created_utc, reverse=True)
            return op_responses[0] if len(op_responses) > 0 else None
