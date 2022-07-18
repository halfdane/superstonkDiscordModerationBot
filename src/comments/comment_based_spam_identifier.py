import re
from datetime import datetime, timedelta

from simhash import Simhash, SimhashIndex

from comments.comment_body_repository import CommentBodiesRepository
from comments.comment_repository import Comments
from helper.links import permalink
from reddit_item_handler import Handler


class CommentBasedSpamIdentifier(Handler):

    def __init__(self, comment_repo: Comments = None,
                 comment_body_repo: CommentBodiesRepository = None,
                 readonly_reddit=None, send_discord_message=None,
                 superstonk_moderators=None, **kwargs):
        super().__init__()
        self.persist_comments = comment_repo
        self.comment_body_repo = comment_body_repo
        self.readonly_reddit = readonly_reddit
        self.send_discord_message = send_discord_message
        self.superstonk_moderators = superstonk_moderators

    def wot_doing(self):
        return "Identify spammers"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.warning(self.wot_doing())

    async def take(self, item):
        body = getattr(item, 'body', '')
        await self.comment_body_repo.store(item.id, body)

    def get_features(self, s):
        width = 3
        s = s.lower()
        s = re.sub(r'[^\w]+', '', s)
        return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]

    async def find_spammers(self):
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        ids = await self.persist_comments.ids(since=last_hour)

        index = SimhashIndex(objs={}, k=3)

        for id in ids:
            body = await self.comment_body_repo.fetch_body(id)

            features = self.get_features(body)
            if len(features) == 1 and features[0] == "":
                self._logger.info(f"ignoring comment without text: {body}")
                return

            simhash = Simhash(features)
            dups = index.get_near_dups(simhash)

            dup_items = [permalink(await self.readonly_reddit.comment(id=dub_id)) for dub_id in dups]
            if len(dup_items) > 3:
                self.send_discord_message(
                    description_beginning="Is this spam?",
                    fields={"duplicates": dup_items},
                    auto_clean=False
                )

            index.add(id, simhash)
