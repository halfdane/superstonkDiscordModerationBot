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
        now = datetime.utcnow().timestamp()

        def __comment_to_db(comment):
            try:
                mod_removed = comment.removed or (getattr(comment, "ban_note", None) is not None)
                return (
                    comment.id,
                    getattr(comment.author, 'name', str(comment.author)),
                    comment.created_utc,
                    f"{now}:{comment.score}",
                    f"{now}" if comment.body == '[deleted]' else None,
                    f"{now}" if mod_removed else None,
                )
            except AttributeError as e:
                self._logger.exception(f'this caused a problem: [{comment}]')
                raise e

        comments = [__comment_to_db(item) for item in comments]

        async with aiosqlite.connect(self.database) as db:
            await db.executemany('''
                    INSERT INTO COMMENTS(id, author, created_utc, score, deleted, mod_removed) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET 
                    score=score || " " || excluded.score, 
                    deleted=excluded.deleted, 
                    mod_removed=excluded.mod_removed
                    ''', comments)
            await db.commit()

    async def fetch(self, since: datetime = None, deleted_not_removed=False):
        async with aiosqlite.connect(self.database) as db:
            statement = 'select id, author, created_utc, score, deleted, mod_removed from COMMENTS'
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
            Comment = namedtuple("Comment", "id author created_utc score deleted mod_removed")
            async with db.execute(statement, condition_parameters) as cursor:
                def __split_scores(scores):
                    return [(datetime.utcfromtimestamp(float(check.split(":")[0])), int(check.split(":")[1]))
                            for check in scores.split(" ")]
                return [Comment(row[0], Author(row[1]), row[2], __split_scores(row[3]), row[4], row[5]) async for row in cursor]

    async def fullnames(self, since: datetime = None):
        async with aiosqlite.connect(self.database) as db:
            statement = 'select id from COMMENTS'
            condition_statements = []
            condition_parameters = {}
            if since is not None:
                condition_statements.append('created_utc >:since')
                condition_parameters['since'] = since.timestamp()

            if len(condition_statements) > 0:
                statement = f'{statement} where {" and ".join(condition_statements)};'

            async with db.execute(statement, condition_parameters) as cursor:
                return [f"t1_{row[0]}" async for row in cursor]

    async def find_mass_deleters(self, since: datetime):
        statement = """
            select author, count(*) as c from COMMENTS 
            where deleted is not NULL and created_utc >:since 
            group by author having c>3"""
        async with aiosqlite.connect(self.database) as db:
            async with db.execute(statement, {'since', since.timestamp()}) as cursor:
                return [(row[0], row[1]) async for row in cursor]

    async def contains(self, comment):
        async with aiosqlite.connect(self.database) as db:
            async with db.execute('select count(*) from COMMENTS where id=:id',
                                  {'id': comment.id}) as cursor:
                rows = [row async for row in cursor]
                return rows[0][0] >= 1

