import logging
import sqlite3
from datetime import datetime, timedelta

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
                              'SUBMISSION (hour, type, count, PRIMARY KEY (hour, type) );')

    async def shutdown(self):
        await self.db.close()

    async def store_stats(self, stats):
        db_stats = [(item.hour.timestamp(), item.type, item.count) for item in stats]

        await self.db.executemany('''
                INSERT INTO SUBMISSION(hour, type, count) VALUES (?, ?, ?)
                ON CONFLICT(hour, type) DO UPDATE SET count=excluded.count
                ''', db_stats)
        await self.db.commit()

    async def fetch_stats(self):
        async with self.db.execute('''
                    select strftime('%Y-%m-%d', hour, 'unixepoch') as day, type, sum(count) as cnt 
                    From SUBMISSION 
                    group by day, type 
                    having hour > 1646089200 and hour < :droplast 
                    order by day, type
                ''', {"droplast": (datetime.now() - timedelta(days=1)).timestamp()}) as cursor:
            return [(datetime.strptime(row[0], "%Y-%m-%d"), row[1], row[2]) async for row in cursor]
