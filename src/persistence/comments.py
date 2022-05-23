import logging
from collections import namedtuple
from datetime import datetime
from os.path import expanduser
from typing import List
from asyncpraw.models.reddit.comment import Comment

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
                             'COMMENTS (id PRIMARY KEY, author, created_utc, deleted, mod_removed);')
            await db.execute('CREATE TABLE if not exists '
                             'SCORES(id NOT NULL , updated_utc real NOT NULL , score INT, PRIMARY KEY (id, updated_utc));')

    async def store(self, comments: List[Comment]):
        now = datetime.utcnow().timestamp()

        def __comment_to_db(comment):
            mod_removed = comment.removed or (getattr(comment, "ban_note", None) is not None)
            return (
                comment.id,
                getattr(comment.author, 'name', str(comment.author)),
                comment.created_utc,
                now if comment.body == '[deleted]' else None,
                now if mod_removed else None,
            )

        def __score_to_db(item):
            return item.id, now, item.score

        db_scores = [__score_to_db(item) for item in comments]
        db_comments = [__comment_to_db(item) for item in comments]
        async with aiosqlite.connect(self.database) as db:
            await db.executemany('''
                    INSERT INTO COMMENTS(id, author, created_utc, deleted, mod_removed) 
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET 
                    deleted=excluded.deleted, 
                    mod_removed=excluded.mod_removed
                    ''', db_comments)
            await db.executemany('INSERT INTO SCORES(id, updated_utc, score) VALUES (?, ?, ?)', db_scores)

            await db.commit()

    async def fetch(self, since: datetime = None, deleted_not_removed=False):
        async with aiosqlite.connect(self.database) as db:
            statement = 'select id, author, created_utc, deleted, mod_removed from COMMENTS'
            condition_statements = []
            condition_parameters = {}
            if since is not None:
                condition_statements.append('created_utc >:since')
                condition_parameters['since'] = since.timestamp()

            if deleted_not_removed:
                condition_statements.append('deleted is not NULL and mod_removed is NULL')

            if len(condition_statements) > 0:
                statement = f'{statement} where {" and ".join(condition_statements)};'

            Author = namedtuple("Author", "name")
            Comment = namedtuple("Comment", "id author created_utc deleted mod_removed")
            async with db.execute(statement, condition_parameters) as cursor:
                return [Comment(row[0], Author(row[1]), row[2], row[3], row[4]) async for row in cursor]

    async def fullnames(self, since: datetime):
        async with aiosqlite.connect(self.database) as db:
            statement = 'select id from COMMENTS where created_utc >:since;'
            timestamp = since.timestamp()
            print(f"parameter is {timestamp} of type {type(timestamp)}")
            async with db.execute(statement, {'since': timestamp}) as cursor:
                return [f"t1_{row[0]}" async for row in cursor]

    async def find_authors_with_removed_negative_comments(self, since: datetime):
        statement = """
            select distinct c.author, c.id, min(s.score) 
            from COMMENTS as c left join SCORES as s on c.id == s.id 
            where s.score<0 and c.deleted is not NULL and c.deleted>:since
            group by c.id order by c.author, c.deleted;
            """
        async with aiosqlite.connect(self.database) as db:
            async with db.execute(statement, {'since': since.timestamp()}) as cursor:
                return [(row[0], row[1], row[2]) async for row in cursor]

    async def find_authors_with_negative_comments(self, limit, since: datetime):
        statement = """
            select distinct c.author, c.id, min(s.score), count(*)
            from COMMENTS as c left join SCORES as s on c.id == s.id 
            where s.score<:limit and s.created_utc>:since
            group by c.id order by c.author, c.deleted;
            """
        async with aiosqlite.connect(self.database) as db:
            async with db.execute(statement, {'since': since.timestamp(), 'limit': limit}) as cursor:
                return [(row[0], row[1], row[2]) async for row in cursor]

    async def contains(self, comment):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select count(*) from COMMENTS where id=:id',
                                  {'id': comment.id}) as cursor:
                rows = [row async for row in cursor]
                return rows[0][0] >= 1


t = '''
drop table SCORES;

CREATE TABLE if not exists 
 SCORES(id NOT NULL , updated_utc real NOT NULL , score INT, PRIMARY KEY (id, updated_utc));

insert into SCORES 
WITH RECURSIVE split(eid, label, str) AS (
    SELECT id, '', score||' ' FROM COMMENTS
    UNION ALL SELECT
    eid,
    substr(str, 0, instr(str, ' ')),
    substr(str, instr(str, ' ')+1)
    FROM split WHERE str!=''
) 
SELECT eid as id, cast(substr(label, 0, instr(label, ':')) as real) as updated_utc, cast(substr(label, instr(label, ':')+1) as integer) as score
FROM split
WHERE label!='';

'''

