import re
from datetime import datetime, timedelta

from simhash import Simhash, SimhashIndex

from comments.comment_body_repository import CommentBodiesRepository
from comments.comment_repository import Comments
from helper.item_helper import permalink
from reddit_item_handler import Handler


class CommentBasedSpamIdentifier(Handler):
    drs_witnesses = ["Rockets2theMoon", "PhillyTheBeaut", "KnightsBridge_1896", "WrongScratch", "No-Vacation-654",
                     "SimpleJack2021", ]

    def __init__(self, comment_repo: Comments = None,
                 comment_body_repo: CommentBodiesRepository = None,
                 readonly_reddit=None, send_discord_message=None,
                 superstonk_moderators=None, **kwargs):
        super().__init__()
        self.comment_repo = comment_repo
        self.comment_body_repo = comment_body_repo
        self.readonly_reddit = readonly_reddit
        self.send_discord_message = send_discord_message
        self.superstonk_moderators = superstonk_moderators

    def wot_doing(self):
        return "Identify spammers"

    async def on_ready(self, scheduler, **kwargs):
        self._logger.warning(self.wot_doing())
        scheduler.add_job(self.report_spammers, "cron", hour="*", next_run_time=datetime.now())

    async def take(self, item):
        body = getattr(item, 'body', '')
        await self.comment_body_repo.store(item.id, body)

    def get_features(self, s):
        width = 3
        s = s.lower()
        s = re.sub(r'[^\w]+', '', s)
        return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]

    async def report_spammers(self):
        spammers = await self.find_spammers()
        for k, v in spammers.items():
            await self.send_discord_message(
                description_beginning="Is this a spammer?",
                author=k,
                fields={
                    "comment": v[1],
                    "duplicates": v[0],
                }
            )

    async def find_spammers(self):
        self._logger.info("Starting to hunt for spammers")
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        ids = await self.comment_repo.ids(since=last_hour)

        index = SimhashIndex(objs={}, k=5)
        hashes = set()

        for i, id in enumerate(ids):
            author = (await self.comment_repo.fetch(id=id))[0].author.name
            if author in self.superstonk_moderators or author in self.drs_witnesses:
                continue

            body = await self.comment_body_repo.fetch_body(id)
            if body is None or len(body) == 0:
                body = ""
            features = self.get_features(body)
            if len(features) == 1 and features[0] == "":
                continue

            simhash = Simhash(features)
            dups = index.get_near_dups(simhash)

            if len(dups) >= 3:
                hashes.add(simhash.value)
            index.add(f"t1_{id}", simhash)

        spammer = {}
        for h in hashes:
            s = Simhash(h)
            dups = index.get_near_dups(s)
            comments = [c async for c in self.readonly_reddit.info(dups)]
            author = comments[0].author
            body = comments[0].body[:100]
            if all([c.author == author for c in comments]):
                spammer[author] = ([permalink(c) for c in comments], body)

        return spammer
