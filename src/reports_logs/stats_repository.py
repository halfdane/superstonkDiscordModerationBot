import logging
import sqlite3
from datetime import datetime

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
                              'COMMENTS (day PRIMARY KEY, count);')

        await self.db.execute('CREATE TABLE if not exists '
                              'POSTS (day, flair, count, PRIMARY KEY (day, flair) );')

    async def shutdown(self):
        await self.db.close()

    async def store_comment_stats(self, comment_stats):
        db_stats = [(item.day, item.comment_count) for item in comment_stats]

        await self.db.executemany('''
                INSERT INTO COMMENTS(day, count) VALUES (?, ?)
                ON CONFLICT(day) DO UPDATE SET count=excluded.count
                ''', db_stats)
        await self.db.commit()

    async def store_post_stats(self, post_stats):
        db_stats = [(item.day, item.flair, item.post_count) for item in post_stats]

        await self.db.executemany('''
                INSERT INTO POSTS(day, flair, count) VALUES (?, ?, ?)
                ON CONFLICT(day, flair) DO UPDATE SET count=excluded.count
                ''', db_stats)
        await self.db.commit()

    async def fetch_stats(self):
        rows = {}
        async with self.db.execute('select day, count from COMMENTS ') as cursor:
            rows['comments'] = [[datetime.strptime(row[0], "%Y%m%d"), row[1]] async for row in cursor]
        async with self.db.execute('select flair, day, count from POSTS where count > 1') as cursor:
            rows['posts'] = [(row[0] if row[0] is not None else "", datetime.strptime(row[1], "%Y%m%d"), row[2]) async for row in cursor]

        return rows
