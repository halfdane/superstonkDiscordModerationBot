import logging

import aiosqlite

from helper.moderation_bot_configuration import CONFIG_HOME

POSTS_DB = f"{CONFIG_HOME}/flairy_comments.db"


class FlairyComments:
    def __init__(self, database=POSTS_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)

    async def on_ready(self, **_):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('CREATE TABLE if not exists '
                             'FLAIRY_COMMENTS (id PRIMARY KEY, body);')

    async def push(self, comment_id, body):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('''
                    INSERT INTO FLAIRY_COMMENTS(id, body) VALUES (?, ?) ON CONFLICT(id) DO NOTHING
                    ''', (comment_id, body))
            await db.commit()

    async def pop_body(self, comment_id):
        async with aiosqlite.connect(self.database) as db:
            cursor = await db.execute('select body from FLAIRY_COMMENTS where id=:comment_id',
                                      {'comment_id': comment_id})
            all_rows = [row[0] async for row in cursor]
            if len(all_rows) == 0:
                return None

            comment_body = all_rows[0]
            await cursor.close()
            await db.execute('delete from FLAIRY_COMMENTS where id = :comment_id',
                             {'comment_id': comment_id})
            await db.commit()

            return comment_body
