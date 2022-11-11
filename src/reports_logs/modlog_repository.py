import logging
from datetime import datetime

import aiosqlite

from helper.moderation_bot_configuration import CONFIG_HOME

COMMENTS_DB = f"{CONFIG_HOME}/modlog.db"


class ModlogRepository:
    def __init__(self, database=COMMENTS_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)

    async def on_ready(self, **_):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('CREATE TABLE if not exists modlog (id PRIMARY KEY, created_utc, action, mod);')

    async def store(self, logs):
        db_logs = [(log.id, log.created_utc, log.action, log._mod) for log in logs]
        async with aiosqlite.connect(self.database) as db:
            await db.executemany('''
                        INSERT INTO modlog(id, created_utc, action, mod) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO NOTHING
                        ''', db_logs)
            await db.commit()

    async def fetch_action(self, id):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select action from modlog where id=:id',
                                  {'id': id}) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def remove(self, ids):
        async with aiosqlite.connect(self.database) as db:
            statement = 'delete from modlog where id = :id'
            for id in ids:
                await db.execute(statement, {'id': id})
            await db.commit()

    async def contains(self, log):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select count(*) from modlog where id=:id',
                                  {'id': log.id}) as cursor:
                rows = [row async for row in cursor]
                return rows[0][0] >= 1

