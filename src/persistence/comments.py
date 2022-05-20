import logging
from collections import namedtuple
from datetime import datetime
from os.path import expanduser

import aiosqlite

home = expanduser("~")
COMMENTS_DB = f"{home}/comments.db"


class Comments:
    def __init__(self, database=COMMENTS_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)

    async def on_ready(self, **_):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('CREATE TABLE if not exists '
                             'COMMENTS (id PRIMARY KEY, author, created_utc, score, deleted, mod_removed);')

    async def store(self, comments):
        def __comment_to_db(comment):
            try:
                return (
                    comment.permalink,
                    getattr(comment.author, 'name', str(comment.author)),
                    comment.created_utc,
                    comment.score,
                    comment.body == '[deleted]',
                    comment.removed,
                )
            except AttributeError as e:
                self._logger.exception(f'this caused a problem: [{comment}]')
                raise e

        comments = [__comment_to_db(item) for item in comments]

        async with aiosqlite.connect(self.database) as db:
            await db.executemany('''
                    INSERT INTO COMMENTS(id, author, created_utc, score, deleted, mod_removed) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET score=excluded.score
                    ''', comments)
            await db.commit()

    async def fetch(self, since: datetime = None):
        async with aiosqlite.connect(self.database) as db:
            statement = 'select id, author, created_utc, score, deleted, mod_removed from COMMENTS'
            condition_statements = []
            condition_parameters = {}
            if since is not None:
                condition_statements.append('created_utc >:since')
                condition_parameters['since'] = since.timestamp()

            if len(condition_statements) > 0:
                statement = f'{statement} where {" and ".join(condition_statements)};'

            Author = namedtuple("Author", "name")
            Comment = namedtuple("Comment", "permalink author created_utc score deleted mod_removed")
            async with db.execute(statement, condition_parameters) as cursor:
                return [Comment(row[0], Author(row[1]), row[2], row[3], row[4] != 0, row[5] != 0) async for row in cursor]

    async def contains(self, post):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select count(*) from COMMENTS where id=:permalink',
                                  {'permalink': post.permalink}) as cursor:
                rows = [row async for row in cursor]
                return rows[0][0] >= 1

