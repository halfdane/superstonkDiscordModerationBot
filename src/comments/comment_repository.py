import logging
from collections import namedtuple
from datetime import datetime
from typing import List

import aiosqlite
from asyncpraw.models.reddit.comment import Comment

from helper.item_helper import author
from helper.moderation_bot_configuration import CONFIG_HOME

COMMENTS_DB = f"{CONFIG_HOME}/comments.db"


class Comments:
    def __init__(self, database=COMMENTS_DB):
        self.database = database
        self._logger = logging.getLogger(self.__class__.__name__)

    async def on_ready(self, **_):
        async with aiosqlite.connect(self.database) as db:
            await db.execute('CREATE TABLE if not exists '
                             'COMMENTS (id PRIMARY KEY, author, created_utc, deleted, mod_removed, updated_utc, score);')

    async def store(self, comments: List[Comment]):
        now = datetime.utcnow().timestamp()

        def __comment_to_db(comment):
            mod_removed = comment.removed or (getattr(comment, "ban_note", None) is not None)
            return (
                comment.id,
                author(comment),
                comment.created_utc,
                now if comment.body == '[deleted]' else None,
                now if mod_removed else None,
                now,
                comment.score
            )

        db_comments = [__comment_to_db(item) for item in comments]
        async with aiosqlite.connect(self.database) as db:
            await db.executemany('''
                    INSERT INTO COMMENTS(id, author, created_utc, deleted, mod_removed, updated_utc, score) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET 
                    deleted=excluded.deleted, 
                    mod_removed=excluded.mod_removed,
                    updated_utc=excluded.updated_utc,
                    score = excluded.score
                    ''', db_comments)
            await db.commit()

    async def fetch(self, since: datetime = None,
                    deleted_not_removed=False, author=None,
                    id=None):
        async with aiosqlite.connect(self.database) as db:
            statement = 'select id, author, created_utc, deleted, mod_removed, updated_utc, score from COMMENTS'
            condition_statements = []
            condition_parameters = {}
            if since is not None:
                condition_statements.append('created_utc >:since')
                condition_parameters['since'] = since.timestamp()

            if author is not None:
                condition_statements.append('author = :author')
                condition_parameters['author'] = str(author)

            if id is not None:
                condition_statements.append('id = :id')
                condition_parameters['id'] = str(id)

            if deleted_not_removed:
                condition_statements.append('deleted is not NULL and mod_removed is NULL')

            if len(condition_statements) > 0:
                statement = f'{statement} where {" and ".join(condition_statements)};'

            Author = namedtuple("Author", "name")
            Comment = namedtuple("Comment", "id author created_utc deleted mod_removed updated_utc score")
            async with db.execute(statement, condition_parameters) as cursor:
                return [Comment(row[0], Author(row[1]), row[2], row[3], row[4], row[5], row[6]) async for row in cursor]

    async def ids(self, since: datetime, before: datetime = None):
        statement = 'select id from COMMENTS'
        condition_statements = []
        condition_parameters = {}
        if since is not None:
            condition_statements.append('created_utc >:since')
            condition_parameters['since'] = since.timestamp()

        if before is not None:
            condition_statements.append('created_utc <:before')
            condition_parameters['before'] = before.timestamp()

        if len(condition_statements) > 0:
            statement = f'{statement} where {" and ".join(condition_statements)};'

        async with aiosqlite.connect(self.database) as db:
            async with db.execute(statement, condition_parameters) as cursor:
                return [row[0] async for row in cursor]

    async def find_authors_with_removed_negative_comments(self, since: datetime):
        statement = """
            select distinct author, id, score 
            from COMMENTS  
            where score<0 and deleted is not NULL and created_utc>:since
            order by author, deleted;
            """
        async with aiosqlite.connect(self.database) as db:
            async with db.execute(statement, {'since': since.timestamp()}) as cursor:
                return [(row[0], row[1], row[2]) async for row in cursor]

    async def find_authors_with_negative_comments(self, limit, since: datetime):
        statement = """
            select distinct author, id, score
            from COMMENTS 
            where score<:limit and created_utc>:since
            order by author, deleted;
            """
        async with aiosqlite.connect(self.database) as db:
            async with db.execute(statement, {'since': since.timestamp(), 'limit': limit}) as cursor:
                return [(row[0], row[1], row[2]) async for row in cursor]

    async def heavily_downvoted_comments(self, limit, since: datetime):
        statement = """
            select id
            from COMMENTS  
            where score<:limit and created_utc>:since and deleted is NULL;
            """
        async with aiosqlite.connect(self.database) as db:
            async with db.execute(statement, {'since': since.timestamp(), 'limit': limit}) as cursor:
                return [row[0] async for row in cursor]

    async def contains(self, comment):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select count(*) from COMMENTS where id=:id',
                                  {'id': comment.id}) as cursor:
                rows = [row async for row in cursor]
                return rows[0][0] >= 1

    async def count(self, since, until):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select count(*) from COMMENTS where created_utc >:since and created_utc <:until',
                                  {'since': since.timestamp(), 'until': until.timestamp()}) as cursor:
                rows = [row async for row in cursor]
                return rows[0][0]

    async def top(self, since, until):
        async with aiosqlite.connect(self.database) as db:
            statement = '''
                    select id from COMMENTS  
                    where created_utc >:since and created_utc <:until
                    order by score desc limit 10;'''
            params = {'since': since.timestamp(), 'until': until.timestamp()}
            self._logger.debug(f"executing {statement} with params {params}")
            async with db.execute(statement, params) as cursor:
                return [row[0] async for row in cursor]

    async def oldest(self):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select created_utc from COMMENTS ORDER by created_utc limit 1') as cursor:
                return [row[0] async for row in cursor][0]

    async def remove(self, ids):
        async with aiosqlite.connect(self.database) as db:
            statement = 'delete from COMMENTS where id = :id'
            for id in ids:
                await db.execute(statement, {'id': id})
            await db.commit()
