from collections import namedtuple
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio
from freezegun import freeze_time

from comments.comment_repository import Comments

test_db = f"some_comment_test_db.db"

a_timestamp = 1653125353.78856


def a_comment(num, id=None, author=None, created=None, deleted=None, mod_removed=None):
    return id if id is not None else f"id_{num}", \
           author if author is not None else f"auth{num}", \
           created if created is not None else f"date{num}", \
           deleted, \
           mod_removed,


def a_score(num, id=None, updated=None, score=None):
    return id if id is not None else f"id_{num}", \
           updated if updated is not None else a_timestamp, \
           score if score is not None else num


async def add_test_data(comments, scores):
    async with aiosqlite.connect(test_db) as db:
        await db.executemany('''INSERT INTO COMMENTS(id, author, created_utc, deleted, mod_removed) 
                    VALUES (?, ?, ?, ?, ?)''', comments)
        await db.executemany('''INSERT INTO SCORES(id, updated_utc, score) 
                    VALUES (?, ?, ?)''', scores)
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
                assert rows == ['COMMENTS', 'SCORES']

            async with db.execute(
                    "select sql from sqlite_master where type = 'table' and name = 'COMMENTS';") as cursor:
                rows = [row[0] async for row in cursor]
                assert rows == [
                    'CREATE TABLE COMMENTS (id PRIMARY KEY, author, created_utc, deleted, mod_removed)']
            async with db.execute(
                    "select sql from sqlite_master where type = 'table' and name = 'SCORES';") as cursor:
                rows = [row[0] async for row in cursor]
                assert rows == [
                    'CREATE TABLE SCORES(id NOT NULL , updated_utc real NOT NULL , score INT, PRIMARY KEY (id, updated_utc))']

    @pytest.mark.asyncio
    async def test_store(self):
        # given
        testee = Comments(test_db)

        Author = namedtuple("Author", "name")
        Comment = namedtuple("Commment", "id author created_utc body score removed")
        store_posts = [
            Comment("id_1", Author("auth1"), "date1", "[deleted]", "score1", False),
            Comment("id_2", Author("auth2"), "date2", "body2", "score2", True),
            Comment("id_3", Author("auth3"), "date3", "body3", "score3", False),
        ]

        # when
        update_timestamp = datetime(2022, 4, 17, tzinfo=timezone.utc)
        with freeze_time(update_timestamp):
            await testee.store(store_posts)

        # then
        async with aiosqlite.connect(test_db) as db:
            async with db.execute("select * from COMMENTS") as cursor:
                rows = [row async for row in cursor]
                assert len(rows) == 3
                assert a_comment(1, deleted=update_timestamp.timestamp(), mod_removed=None) in rows
                assert a_comment(2, deleted=None, mod_removed=update_timestamp.timestamp()) in rows
                assert a_comment(3, deleted=None, mod_removed=None) in rows

            async with db.execute("select * from SCORES") as cursor:
                rows = [row async for row in cursor]
                assert len(rows) == 3
                assert a_score(1, updated=update_timestamp.timestamp(), score="score1") in rows
                assert a_score(2, updated=update_timestamp.timestamp(), score="score2") in rows
                assert a_score(3, updated=update_timestamp.timestamp(), score="score3") in rows

    @pytest.mark.asyncio
    async def test_read_all(self):
        # given
        await add_test_data([a_comment(1), a_comment(2), a_comment(3)], [a_score(1), a_score(2), a_score(3)])

        # when
        testee = Comments(test_db)
        comments = await testee.fetch()

        # then
        assert len(comments) == 3
        for i in range(3):
            assert comments[i].id == f"id_{i + 1}"
            assert comments[i].author.name == f"auth{i + 1}"
            assert comments[i].created_utc == f"date{i + 1}"
            assert comments[i].deleted is None
            assert comments[i].mod_removed is None

    @pytest.mark.asyncio
    async def test_read_with_multiple_scores(self):
        # given
        await add_test_data([a_comment(1)], [a_score(1, updated=1653118753.0, score=2), a_score(1, updated=1653118802.0, score=6)])

        # when
        testee = Comments(test_db)
        comments = await testee.fetch()

        # then
        assert len(comments) == 1
        assert comments[0].id == f"id_1"
        assert comments[0].author.name == f"auth1"
        assert comments[0].created_utc == f"date1"
        assert comments[0].deleted is None
        assert comments[0].mod_removed is None

    @pytest.mark.asyncio
    async def test_read_after(self):
        # given
        now = datetime.utcnow()
        last_week = now - timedelta(weeks=1)
        three_days_ago = now - timedelta(days=3)
        two_days_ago = now - timedelta(days=2)

        await add_test_data([a_comment(1, created=three_days_ago.timestamp()),
                             a_comment(2, created=last_week.timestamp(), id='old'),
                             a_comment(3, created=two_days_ago.timestamp())],
                            [])

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
        await add_test_data([a_comment(1), a_comment(2), a_comment(3), a_comment(4)], [])

        # when / then
        CommentWithId = namedtuple("Comment", "id")
        assert await testee.contains(CommentWithId('id_1')) is True
        assert await testee.contains(CommentWithId('id_7')) is False

    @pytest.mark.asyncio
    async def test_update_existing(self):
        # given
        testee = Comments(test_db)
        Author = namedtuple("Author", "name")
        Comment = namedtuple("Commment", "id author created_utc body score removed")
        store_posts = [
            Comment("id_1", Author("auth1"), "date1", "[deleted]", "score1", False),
            Comment("id_2", Author("auth2"), "date2", "body2", "score2", True),
            Comment("id_3", Author("auth3"), "date3", "body3", "score3", False),
        ]

        created = datetime(2022, 1, 24, tzinfo=timezone.utc)
        with freeze_time(created):
            await testee.store(store_posts)

        # when
        updated = datetime(2022, 1, 28, tzinfo=timezone.utc)
        with freeze_time(updated):
            await testee.store([Comment("id_1", Author("auth1"), "date1", "something", "score_new", True)])

        # then
        async with aiosqlite.connect(test_db) as db:
            async with db.execute("select * from COMMENTS where id='id_1';") as cursor:
                rows = [row async for row in cursor]
                assert rows == [a_comment(1, deleted=None, mod_removed=updated.timestamp())]
            async with db.execute("select * from SCORES where id='id_1';") as cursor:
                rows = [row async for row in cursor]
                assert rows == [a_score(1, updated=created.timestamp(), score="score1"),
                                a_score(1, updated=updated.timestamp(), score="score_new")]

    @pytest.mark.asyncio
    async def test_fetch_ids(self):
        # given
        now = datetime.utcnow()
        last_week = now - timedelta(weeks=1)
        three_days_ago = now - timedelta(days=3)
        two_days_ago = now - timedelta(days=2)

        await add_test_data([a_comment(1, created=three_days_ago.timestamp()),
                             a_comment(2, created=last_week.timestamp(), id='old'),
                             a_comment(3, created=two_days_ago.timestamp())],
                            [])

        # when
        four_days_ago = now - timedelta(days=4)
        testee = Comments(test_db)
        comments = await testee.ids(since=four_days_ago)

        # then
        assert len(comments) == 2
        assert comments[0] == f"id_1"
        assert comments[1] == f"id_3"

