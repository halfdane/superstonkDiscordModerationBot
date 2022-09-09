import logging
import sqlite3

import aiosqlite

from helper.moderation_bot_configuration import CONFIG_HOME

STATISTICS_DB = f"{CONFIG_HOME}/statistics.db"


class StatisticsRepository:

    def __init__(self, database=STATISTICS_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)
        self.db = None

    async def on_ready(self, **_):
        self.db = await aiosqlite.connect(self.database, detect_types=sqlite3.PARSE_DECLTYPES)
        self.db.row_factory = sqlite3.Row
        await self.db.execute('CREATE TABLE if not exists '
                              'COMMENTS (day PRIMARY KEY, comment_count);')

    async def shutdown(self):
        await self.db.close()

    async def store_comment_stats(self, comment_stats):
        db_stats = [(item.day, item.comment_count) for item in comment_stats]
        async with aiosqlite.connect(self.database) as db:
            await db.executemany('''
                    INSERT INTO COMMENTS(day, comment_count) VALUES (?, ?)
                    ON CONFLICT(day) DO UPDATE SET comment_count=excluded.comment_count
                    ''', db_stats)
            await db.commit()

    async def fetch_comment_stats(self):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select * from COMMENTS ') as cursor:
                return [row async for row in cursor]
