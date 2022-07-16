import logging
from collections import namedtuple
from datetime import datetime
from typing import List

import aiosqlite
from asyncpraw.models.reddit.comment import Comment

from helper.moderation_bot_configuration import CONFIG_HOME

COMMENT_BODIES_DB = f"{CONFIG_HOME}/comment_bodies.db"


class CommentBodiesRepository:
    def __init__(self, database=COMMENT_BODIES_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)

    async def on_ready(self, **_):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('CREATE TABLE if not exists '
                             'COMMENT_BODIES (id PRIMARY KEY, body);')

    async def store(self, comment_id, body):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('INSERT INTO COMMENT_BODIES(id, body) VALUES (?, ?) ON CONFLICT(id) DO NOTHING',
                             (comment_id, body))
            await db.commit()

    async def fetch_body(self, comment_id):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select body from COMMENT_BODIES where id=:comment_id',
                                  {'comment_id': comment_id}) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def remove(self, ids):
        async with aiosqlite.connect(self.database) as db:
            statement = 'delete from COMMENT_BODIES where id = :id'
            for id in ids:
                await db.execute(statement, {'id': id})
            await db.commit()
