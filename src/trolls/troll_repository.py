import logging

import aiosqlite

from helper.moderation_bot_configuration import CONFIG_HOME

POSTS_DB = f"{CONFIG_HOME}/trolls.db"


class TrollRepository:
    def __init__(self, database=POSTS_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)

    async def on_ready(self, **_):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('create table if not exists trolls (USERNAME, SOURCE, PRIMARY KEY(USERNAME, SOURCE));')

    async def push(self, reddit_item):
        if reddit_item.author is not None:
            async with aiosqlite.connect(self.database) as db:
                meltie = reddit_item.author.name
                source = reddit_item.subreddit.display_name
                await db.execute('''
                    INSERT INTO trolls(USERNAME, SOURCE) VALUES (?, ?) 
                    ON CONFLICT(USERNAME, SOURCE) DO NOTHING''', (meltie, source))
                await db.commit()

    async def get_troll_source(self, reddit_item):
        if reddit_item.author is None:
            return None

        meltie = reddit_item.author.name
        async with aiosqlite.connect(self.database) as db:
            async with db.execute("select SOURCE from trolls where USERNAME=:username and SOURCE='gme_meltdown'",
                                  {'username': meltie}) as cursor:
                rows = [row async for row in cursor]
                if len(rows) > 0 and len(rows[0]) > 0:
                    return rows[0][0]
                else:
                    return None
