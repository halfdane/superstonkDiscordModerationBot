import logging
from datetime import datetime, timedelta

import chevron

from helper.links import permalink
from reddit_item_handler import Handler


def author(item):
    return getattr(item.author, 'name', str(item.author))


class RequireQvResponse(Handler):
    def __init__(self, qvbot_reddit, post_repo, quality_vote_bot_configuration, automod_configuration, send_discord_message, **kwargs):
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
        self._logger.warning(self.wot_doing())
        scheduler.add_job(self.check_recent_comments, "cron", minute="*")

    async def check_recent_comments(self, ):
        now = datetime.utcnow()
        interval = now - timedelta(minutes=12)
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

        is_link = getattr(post, 'domain', '') != "reddit.com"

        post_requires_response = op_required_comment is not None
        if post_requires_response:
            self._logger.debug(f"Post requires a response: {permalink(post)}")
            qv_comment = await self.get_qv_comment(post)
            latest_op_response = await self.get_latest_op_response(qv_comment, post)
            if latest_op_response is not None:
                user_provided_string = latest_op_response.body
                self._logger.debug(f"Got a response from Op: {user_provided_string}")
                if self.automod_configuration.is_forbidden_user_message(user_provided_string):
                    await latest_op_response.report(f"Cowardly refusing to use prohibited user input: {user_provided_string}")
                else:
                    # use body of response and put it into the qv_body
                    model = {'op_response': user_provided_string}
                    await qv_comment.edit(chevron.render(op_required_comment, model))
            else:
                # if now is over: report or remove post
                created_utc = datetime.utcfromtimestamp(post.created_utc)

                if latest > created_utc:
                    await self.send_discord_message(description_beginning="Removing post due to missing response", item=post)
                    await post.mod.remove(
                        spam=False,
                        mod_note="Automatically removing after timeout without response",
                        fields={'auto_clean': False})
        else:
            self._logger.debug(f"Post with {flair_id} doesn't require a response")


    async def get_qv_comment(self, post):
        qv_user = await self.qvbot_reddit.user.me()
        if len(post.comments) > 0 and post.comments[0].stickied and author(post.comments[0]) == qv_user.name:
            return post.comments[0]
        else:
            raise Exception(f"No qv comment found in {permalink(post)}")

    async def get_latest_op_response(self, qv_comment, post):
        author_name = author(post)
        comments = qv_comment.replies
        await comments.replace_more(limit=None)
        all_replies = await comments.list()
        if len(all_replies) > 0:
            print([c for c in all_replies])
            op_responses = [c for c in all_replies if author_name == author(c)]
            op_responses.sort(key=lambda c: c.created_utc)
            return op_responses[0]



