import logging
from collections import namedtuple
from datetime import datetime
from os.path import expanduser

import aiosqlite

home = expanduser("~")
POSTS_DB = f"{home}/posts.db"


class Posts:
    def __init__(self, database=POSTS_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)

    async def on_ready(self, **_):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('CREATE TABLE if not exists '
                             'POSTS (id PRIMARY KEY, author, flair, created_utc, title, score, count_to_limit);')

    async def store(self, posts):
        def __post_to_db(post):
            try:
                return (
                    post.id,
                    getattr(post.author, 'name', str(post.author)),
                    getattr(post, 'link_flair_text', "NONE"),
                    post.created_utc,
                    post.title,
                    post.score,
                    getattr(post, 'count_to_limit', True)
                )
            except AttributeError as e:
                self._logger.exception(f'this caused a problem: [{post}]')
                raise e

        posts = [__post_to_db(item) for item in posts]

        async with aiosqlite.connect(self.database) as db:
            await db.executemany('''
                    INSERT INTO POSTS(id, author, flair, created_utc, title, score, count_to_limit) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET score=excluded.score
                    ''', posts)
            await db.commit()

    async def fetch(self, author=None, since: datetime = None, only_counting_to_limit=False):
        async with aiosqlite.connect(self.database) as db:
            statement = 'select id, author, flair, created_utc, title, score, count_to_limit from POSTS'
            condition_statements = []
            condition_parameters = {}
            if author is not None:
                condition_statements.append('author=:author')
                condition_parameters['author'] = author

            if since is not None:
                condition_statements.append('created_utc >:since')
                condition_parameters['since'] = since.timestamp()

            if only_counting_to_limit:
                condition_statements.append('count_to_limit')

            if len(condition_statements) > 0:
                statement = f'{statement} where {" and ".join(condition_statements)};'

            Author = namedtuple("Author", "name")
            Post = namedtuple("Post", "id author link_flair_text created_utc title score count_to_limit")
            async with db.execute(statement, condition_parameters) as cursor:
                return [Post(row[0], Author(row[1]), row[2], row[3], row[4], row[5], row[6]) async for row in cursor]

    async def contains(self, post):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select count(*) from POSTS where id=:id',
                                  {'id': post.id}) as cursor:
                rows = [row async for row in cursor]
                return rows[0][0] >= 1

    async def do_not_count_to_limit(self, post):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('UPDATE POSTS set count_to_limit=:count where id=:id',
                             {'count': False, 'id': post.id})
            await db.commit()
