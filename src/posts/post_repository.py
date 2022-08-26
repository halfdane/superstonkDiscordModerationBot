import logging
from collections import namedtuple
from datetime import datetime

import aiosqlite

from helper.item_helper import author
from helper.moderation_bot_configuration import CONFIG_HOME

POSTS_DB = f"{CONFIG_HOME}/posts.db"


class Posts:
    def __init__(self, database=POSTS_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)

    async def on_ready(self, **_):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('CREATE TABLE if not exists '
                             'POSTS (id PRIMARY KEY, author, flair, created_utc, score, count_to_limit, available);')

    async def store(self, posts):
        def __post_to_db(post):
            try:
                return (
                    post.id,
                    author(post),
                    getattr(post, 'link_flair_text', "NONE"),
                    post.created_utc,
                    post.score,
                    getattr(post, 'count_to_limit', True),
                    getattr(post, 'available', True)
                )
            except AttributeError as e:
                self._logger.exception(f'this caused a problem: [{post}]')
                raise e

        posts = [__post_to_db(item) for item in posts]

        async with aiosqlite.connect(self.database) as db:
            await db.executemany('''
                    INSERT INTO POSTS(id, author, flair, created_utc, score, count_to_limit, available) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET score=excluded.score
                    ''', posts)
            await db.commit()

    async def fetch(self,
                    author=None,
                    since: datetime = None,
                    before: datetime = None,
                    only_counting_to_limit=False,
                    ids=None):
        async with aiosqlite.connect(self.database) as db:
            statement = 'select id, author, flair, created_utc, score, count_to_limit, available from POSTS'
            condition_statements = []
            condition_parameters = {}
            if author is not None:
                condition_statements.append('author=:author')
                condition_parameters['author'] = author

            if ids is not None:
                condition_statements.append(f"id in ({', '.join(f':{i}' for i in range(len(ids)))})")
                condition_parameters.update({str(i): id for i, id in enumerate(ids)})

            if since is not None:
                condition_statements.append('created_utc >:since')
                condition_parameters['since'] = since.timestamp()

            if before is not None:
                condition_statements.append('created_utc <=:before')
                condition_parameters['before'] = before.timestamp()

            if only_counting_to_limit:
                condition_statements.append('count_to_limit')

            if len(condition_statements) > 0:
                statement = f'{statement} where {" and ".join(condition_statements)};'

            Author = namedtuple("Author", "name")
            Post = namedtuple("Post", "id author link_flair_text created_utc score count_to_limit available")
            async with db.execute(statement, condition_parameters) as cursor:
                return [Post(row[0], Author(row[1]), row[2], row[3], row[4], row[5], row[6] != '0') async for row in
                        cursor]

    async def contains(self, post):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select count(*) from POSTS where id=:id',
                                  {'id': post.id}) as cursor:
                rows = [row async for row in cursor]
                return rows[0][0] >= 1

    async def count(self, since, until):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select count(*) from POSTS where created_utc >:since and created_utc <:until',
                                  {'since': since.timestamp(), 'until': until.timestamp()}) as cursor:
                rows = [row async for row in cursor]
                return rows[0][0]

    async def top(self, since, until):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('''
                    select id from POSTS 
                    where created_utc >:since and created_utc <:until
                    order by score desc limit 10;''',
                                  {'since': since.timestamp(), 'until': until.timestamp()}) as cursor:
                return [row[0] async for row in cursor]

    async def oldest(self):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select created_utc from POSTS ORDER by created_utc limit 1') as cursor:
                return [row[0] async for row in cursor][0]

    async def flairs(self, since, until):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('''
                    select flair, count(*) as cnt From POSTS  
                    where created_utc >:since and created_utc <:until
                    group by trim(flair) order by cnt desc;''',
                                  {'since': since.timestamp(), 'until': until.timestamp()}) as cursor:
                return [(row[0], row[1]) async for row in cursor]

    async def do_not_count_to_limit(self, post):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('UPDATE POSTS set count_to_limit=:count where id=:id',
                             {'count': False, 'id': post.id})
            await db.commit()
