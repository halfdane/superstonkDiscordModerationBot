import logging
from collections import namedtuple
from datetime import datetime
from os.path import expanduser
from typing import List
from asyncpraw.models.reddit.comment import Comment

import aiosqlite

home = expanduser("~")
COMMENTS_DB = f"{home}/reports.db"


class Reports:
    def __init__(self, database=COMMENTS_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)

    async def on_ready(self, **_):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('CREATE TABLE if not exists '
                             'REPORT_COUNTER (id PRIMARY KEY, num_reports);')

    async def store(self, reports):
        db_reports = [(item.id, item.num_reports) for item in reports]
        async with aiosqlite.connect(self.database) as db:
            await db.executemany('''
                    INSERT INTO REPORT_COUNTER(id, num_reports) VALUES (?, ?)
                    ON CONFLICT(id) DO UPDATE SET num_reports=excluded.num_reports
                    ''', db_reports)
            await db.commit()

    async def contains(self, report):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select count(*) from REPORT_COUNTER where id=:id and num_reports=:num_reports',
                                  {'id': report.id, 'num_reports': report.num_reports }) as cursor:
                rows = [row async for row in cursor]
                return rows[0][0] >= 1
