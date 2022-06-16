from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio

from comments.flairy_comment_repository import FlairyComments

test_db = f"some_flairy_comment_test_db.db"


def a_comment(num):
    return f"id{num}", f"body{num}"


class TestFlairyCommentDatabaseIntegration:

    @pytest_asyncio.fixture(autouse=True)
    async def before_each(self):
        # given
        Path(test_db).unlink(missing_ok=True)
        testee = FlairyComments(test_db)
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
                assert rows == ['FLAIRY_COMMENTS']

            async with db.execute("select sql from sqlite_master where type = 'table' and name = 'FLAIRY_COMMENTS';") as cursor:
                rows = [row[0] async for row in cursor]
                assert rows == [
                    'CREATE TABLE FLAIRY_COMMENTS (id PRIMARY KEY, body)']

    @pytest.mark.asyncio
    async def test_push(self):
        # given
        store_posts = [("id1", "body1"), ("id2", "body2"), ("id3", "body3")]

        # when
        testee = FlairyComments(test_db)
        for p in store_posts:
            await testee.push(p[0], p[1])

        # then
        async with aiosqlite.connect(test_db) as db:
            async with db.execute("select * from FLAIRY_COMMENTS") as cursor:
                rows = [row async for row in cursor]
                assert len(rows) == 3
                assert a_comment(1) in rows
                assert a_comment(2) in rows
                assert a_comment(3) in rows

    @pytest.mark.asyncio
    async def test_pop(self):
        # given
        async with aiosqlite.connect(test_db) as db:
            await db.executemany("INSERT INTO FLAIRY_COMMENTS(id, body) VALUES (?, ?)",
                             [("id1", "body1"), ("id2", "body2"), ("id3", "body3")])
            await db.commit()


        async with aiosqlite.connect(test_db) as db:
            async with db.execute("select * from FLAIRY_COMMENTS") as cursor:
                rows = [row async for row in cursor]
                assert len(rows) == 3
                assert a_comment(1) in rows
                assert a_comment(2) in rows
                assert a_comment(3) in rows

        testee = FlairyComments(test_db)

        # when
        body = await testee.pop_body("id2")

        # then
        assert body == "body2"

        async with aiosqlite.connect(test_db) as db:
            async with db.execute("select * from FLAIRY_COMMENTS") as cursor:
                rows = [row async for row in cursor]
                assert len(rows) == 2
                assert a_comment(1) in rows
                assert a_comment(3) in rows

    @pytest.mark.asyncio
    async def test_pop_missing_entry(self):
        # given
        testee = FlairyComments(test_db)

        # when
        body = await testee.pop_body("id2")

        # then
        assert body == None




