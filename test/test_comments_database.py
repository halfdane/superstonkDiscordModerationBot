from collections import namedtuple
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio

from persistence.comments import Comments

test_db = f"some_comment_test_db.db"


def a_comment(num, id=None, author=None, created=None, score=None, deleted=None, mod_removed=None):
    return id if id is not None else f"id_{num}", \
           author if author is not None else f"auth{num}", \
           created if created is not None else f"date{num}", \
           score if score is not None else f"score{num}", \
           deleted if deleted is not None else False, \
           mod_removed if mod_removed is not None else False,


async def add_test_data(comments):
    async with aiosqlite.connect(test_db) as db:
        await db.executemany('''INSERT INTO COMMENTS(id, author, created_utc, score, deleted, mod_removed) 
                    VALUES (?, ?, ?, ?, ?, ?)''', comments)
        await db.commit()


class TestCommentDatabaseIntegration:

    @pytest_asyncio.fixture(autouse=True)
    async def before_each(self):
        # given
        Path(test_db).unlink(missing_ok=True)
        testee = Comments(test_db)
        await testee.on_ready()

        # actual test
        yield

        # cleanup
        Path(test_db).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_create_initial_table(self):
        # given / when is now in the fixture

        # then
        async with aiosqlite.connect(test_db) as db:
            async with db.execute("select name from sqlite_master where type = 'table';") as cursor:
                rows = [row[0] async for row in cursor]
                assert rows == ['COMMENTS']

            async with db.execute(
                    "select sql from sqlite_master where type = 'table' and name = 'COMMENTS';") as cursor:
                rows = [row[0] async for row in cursor]
                assert rows == [
                    'CREATE TABLE COMMENTS (id PRIMARY KEY, author, created_utc, score, deleted, mod_removed)']

    @pytest.mark.asyncio
    async def test_store(self):
        # given
        Author = namedtuple("Author", "name")
        Comment = namedtuple("Commment", "id author created_utc body score removed")
        store_posts = [
            Comment("id_1", Author("auth1"), "date1", "[deleted]", "score1", False),
            Comment("id_2", Author("auth2"), "date2", "body2", "score2", True),
            Comment("id_3", Author("auth3"), "date3", "body3", "score3", False),
        ]

        # when
        testee = Comments(test_db)
        await testee.store(store_posts)

        # then
        sqlite_true = 1
        sqlite_false = 0

        async with aiosqlite.connect(test_db) as db:
            async with db.execute("select * from COMMENTS") as cursor:
                rows = [row async for row in cursor]
                assert len(rows) == 3
                assert a_comment(1, deleted=sqlite_true, mod_removed=sqlite_false) in rows
                assert a_comment(2, deleted=sqlite_false, mod_removed=sqlite_true) in rows
                assert a_comment(3, deleted=sqlite_false, mod_removed=sqlite_false) in rows

    @pytest.mark.asyncio
    async def test_read_all(self):
        # given
        await add_test_data([a_comment(1), a_comment(2), a_comment(3)])

        # when
        testee = Comments(test_db)
        comments = await testee.fetch()

        # then
        assert len(comments) == 3
        for i in range(3):
            assert comments[i].id == f"id_{i + 1}"
            assert comments[i].author.name == f"auth{i + 1}"
            assert comments[i].created_utc == f"date{i + 1}"
            assert comments[i].score == f"score{i + 1}"
            assert comments[i].deleted is False
            assert comments[i].mod_removed is False

    @pytest.mark.asyncio
    async def test_read_after(self):
        # given
        now = datetime.utcnow()
        last_week = now - timedelta(weeks=1)
        three_days_ago = now - timedelta(days=3)
        two_days_ago = now - timedelta(days=2)

        await add_test_data([a_comment(1, created=three_days_ago.timestamp()),
                             a_comment(2, created=last_week.timestamp(), id='old'),
                             a_comment(3, created=two_days_ago.timestamp())])

        # when
        four_days_ago = now - timedelta(days=4)
        testee = Comments(test_db)
        comments = await testee.fetch(since=four_days_ago)

        # then
        assert len(comments) == 2
        assert comments[0].id == f"id_1"
        assert comments[1].id == f"id_3"


    @pytest.mark.asyncio
    async def test_database_contains(self):
        # given
        testee = Comments(test_db)
        await add_test_data([a_comment(1), a_comment(2), a_comment(3), a_comment(4)])

        # when / then
        CommentWithId = namedtuple("Comment", "id")
        assert await testee.contains(CommentWithId('id_1')) is True
        assert await testee.contains(CommentWithId('id_7')) is False
