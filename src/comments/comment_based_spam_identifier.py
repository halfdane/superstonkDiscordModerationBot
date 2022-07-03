import re

from simhash import Simhash, SimhashIndex

from comments.comment_repository import Comments
from helper.links import permalink
from reddit_item_handler import Handler


class CommentBasedSpamIdentifier(Handler):

    hashes = []

    def __init__(self, comment_repo: Comments = None, readonly_reddit=None, send_discord_message=None,
                 superstonk_moderators=None, **kwargs):
        super().__init__()
        self.persist_comments = comment_repo
        self.readonly_reddit = readonly_reddit
        self.send_discord_message = send_discord_message
        self.superstonk_moderators = superstonk_moderators
        self.index = SimhashIndex(objs={}, k=3)

    def wot_doing(self):
        return "Identify spammers"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.warning(self.wot_doing())

    def get_features(self, s):
        width = 3
        s = s.lower()
        s = re.sub(r'[^\w]+', '', s)
        return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]

    async def take(self, item):
        author = getattr(getattr(item, "author", None), "name", None)
        if author in self.superstonk_moderators:
            self._logger.info("ignoring mod comment")
            return

        body = getattr(item, 'body', '')
        features = self.get_features(body)
        if len(features) == 1 and features[0]=="":
            self._logger.info(f"ignoring comment without text: {body}")
            return

        simhash = Simhash(features)
        dups = self.index.get_near_dups(simhash)

        dup_items = [permalink(await self.readonly_reddit.comment(id=dub_id)) for dub_id in dups]
        if len(dup_items) > 5:
            self.send_discord_message(
                item=item, description_beginning="Is this spam?",
                fields={"duplicates": dup_items})

        self.index.add(item.id, simhash)

