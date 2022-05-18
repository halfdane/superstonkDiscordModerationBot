from collections import namedtuple
from datetime import datetime, timedelta
from pathlib import Path
from pprint import pprint

import aiosqlite
import pytest
import pytest_asyncio

from persistence.posts import Posts

test_db = f"some_test_db.db"


class TestPostDatabaseIntegration:

    @pytest_asyncio.fixture(autouse=True)
    async def before_each(self):
        # given
        Path(test_db).unlink(missing_ok=True)
        testee = Posts(test_db)
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
                assert rows == ['POSTS']

            async with db.execute("select sql from sqlite_master where type = 'table' and name = 'POSTS';") as cursor:
                rows = [row[0] async for row in cursor]
                assert rows == [
                    'CREATE TABLE POSTS (id PRIMARY KEY, author, flair, created_utc, title, score, count_to_limit)']

    @pytest.mark.asyncio
    async def test_store(self):
        # given
        Author = namedtuple("Author", "name")
        PostWithLimit = namedtuple("Post", "permalink author link_flair_text created_utc title score count_to_limit")
        PostWithoutLimit = namedtuple("Post", "permalink author link_flair_text created_utc title score")

        posts = [
            PostWithLimit("perma1", Author("auth1"), "flair1", "date1", "title1", "score1", "cnt1"),
            PostWithoutLimit("perma2", Author("auth2"), "flair2", "date2", "title2", "score2"),
            PostWithLimit("perma3", Author("auth3"), "flair3", "date3", "title3", "score3", "cnt3"),
        ]

        # when
        testee = Posts(test_db)
        await testee.store(posts)

        # then
        async with aiosqlite.connect(test_db) as db:
            async with db.execute("select * from POSTS") as cursor:
                rows = [row async for row in cursor]
                assert len(rows) == 3
                assert ("perma1", "auth1", "flair1", "date1", "title1", "score1", "cnt1") in rows
                assert ("perma2", "auth2", "flair2", "date2", "title2", "score2", True) in rows
                assert ("perma3", "auth3", "flair3", "date3", "title3", "score3", "cnt3") in rows

    @pytest.mark.asyncio
    async def test_read_all(self):
        # given
        async with aiosqlite.connect(test_db) as db:
            posts = [("perma1", "auth1", "flair1", "date1", "title1", "score1", "cnt1"),
                     ("perma2", "auth2", "flair2", "date2", "title2", "score2", "cnt2"),
                     ("perma3", "auth3", "flair3", "date3", "title3", "score3", "cnt3")]
            await db.executemany('''
                        INSERT INTO POSTS(id, author, flair, created_utc, title, score, count_to_limit) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', posts)
            await db.commit()

        # when
        testee = Posts(test_db)
        posts = await testee.fetch()

        # then
        assert len(posts) == 3
        for i in range(3):
            assert posts[i].permalink == f"perma{i + 1}"
            assert posts[i].author.name == f"auth{i + 1}"
            assert posts[i].link_flair_text == f"flair{i + 1}"
            assert posts[i].created_utc == f"date{i + 1}"
            assert posts[i].title == f"title{i + 1}"
            assert posts[i].score == f"score{i + 1}"
            assert posts[i].count_to_limit == f"cnt{i + 1}"

    @pytest.mark.asyncio
    async def test_read_from_user(self):
        # given
        async with aiosqlite.connect(test_db) as db:
            posts = [("perma1", "auth1", "flair1", "date1", "title1", "score1", "cnt1"),
                     ("perma2", "auth2", "flair2", "date2", "title2", "score2", "cnt2"),
                     ("perma3", "auth1", "flair3", "date3", "title3", "score3", "cnt3")]
            await db.executemany('''
                        INSERT INTO POSTS(id, author, flair, created_utc, title, score, count_to_limit)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', posts)
            await db.commit()

        # when
        testee = Posts(test_db)
        posts = await testee.fetch(author="auth1")

        # then
        assert len(posts) == 2
        assert posts[0].permalink == f"perma1"
        assert posts[0].author.name == f"auth1"

        assert posts[1].permalink == f"perma3"
        assert posts[1].author.name == f"auth1"

    @pytest.mark.asyncio
    async def test_read_after(self):
        # given
        now = datetime.utcnow()
        last_week = now - timedelta(weeks=1)
        three_days_ago = now - timedelta(days=3)
        two_days_ago = now - timedelta(days=2)

        async with aiosqlite.connect(test_db) as db:
            posts = [("perma1", "auth1", "flair1", three_days_ago.timestamp(), "title1", "score1", "cnt1"),
                     ("old", "auth2", "flair2", last_week.timestamp(), "title2", "score2", "cnt2"),
                     ("perma3", "auth3", "flair3", two_days_ago.timestamp(), "title3", "score3", "cnt3")]
            await db.executemany('''
                        INSERT INTO POSTS(id, author, flair, created_utc, title, score, count_to_limit)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', posts)
            await db.commit()

        # when
        four_days_ago = now - timedelta(days=4)
        testee = Posts(test_db)
        posts = await testee.fetch(since=four_days_ago)

        # then
        assert len(posts) == 2
        assert posts[0].permalink == f"perma1"
        assert posts[1].permalink == f"perma3"

    @pytest.mark.asyncio
    async def test_read_counting_only(self):
        # given
        async with aiosqlite.connect(test_db) as db:
            posts = [("perma1", "auth1", "flair1", "date1", "title1", "score1", True),
                     ("perma2", "auth2", "flair2", "date2", "title2", "score2", False),
                     ("perma3", "auth3", "flair3", "date3", "title3", "score3", False),
                     ("perma4", "auth4", "flair4", "date4", "title4", "score4", True)]
            await db.executemany('''
                        INSERT INTO POSTS(id, author, flair, created_utc, title, score, count_to_limit) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', posts)
            await db.commit()

        # when
        testee = Posts(test_db)
        posts = await testee.fetch(only_counting_to_limit=True)

        # then
        assert len(posts) == 2
        assert posts[0].permalink == f"perma1"
        assert posts[1].permalink == f"perma4"

    @pytest.mark.asyncio
    async def test_read_author_after(self):
        # given
        now = datetime.utcnow()
        last_week = now - timedelta(weeks=1)
        three_days_ago = now - timedelta(days=3)
        two_days_ago = now - timedelta(days=2)

        async with aiosqlite.connect(test_db) as db:
            posts = [("perma1", "auth1", "flair1", three_days_ago.timestamp(), "title1", "score1", "cnt1"),
                     ("old", "auth2", "flair2", last_week.timestamp(), "title2", "score2", "cnt2"),
                     ("perma3", "auth3", "flair3", two_days_ago.timestamp(), "title3", "score3", "cnt3")]
            await db.executemany('''
                        INSERT INTO POSTS(id, author, flair, created_utc, title, score, count_to_limit)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', posts)
            await db.commit()

        # when
        four_days_ago = now - timedelta(days=4)
        testee = Posts(test_db)
        posts = await testee.fetch(since=four_days_ago, author='auth3')

        # then
        assert len(posts) == 1
        assert posts[0].permalink == f"perma3"

    @pytest.mark.asyncio
    async def test_do_not_count(self):
        # given
        testee = Posts(test_db)
        async with aiosqlite.connect(test_db) as db:
            posts = [("perma1", "auth1", "flair1", "date1", "title1", "score1", True),
                     ("perma2", "auth2", "flair2", "date2", "title2", "score2", False),
                     ("perma3", "auth3", "flair3", "date3", "title3", "score3", True)]
            await db.executemany('''
                        INSERT INTO POSTS(id, author, flair, created_utc, title, score, count_to_limit) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', posts)
            await db.commit()

        posts = await testee.fetch(only_counting_to_limit=True)
        assert len(posts) == 2
        assert posts[0].permalink == f"perma1"
        assert posts[1].permalink == f"perma3"

        # when
        PostWithId = namedtuple("Post", "permalink")

        await testee.do_not_count_to_limit(PostWithId('perma1'))

        # then
        posts = await testee.fetch(only_counting_to_limit=True)
        assert len(posts) == 1
        assert posts[0].permalink == f"perma3"

    @pytest.mark.asyncio
    async def test_database_contains(self):
        # given
        testee = Posts(test_db)
        async with aiosqlite.connect(test_db) as db:
            posts = [("perma1", "auth1", "flair1", "date1", "title1", "score1", True),
                     ("perma2", "auth2", "flair2", "date2", "title2", "score2", False),
                     ("perma3", "auth3", "flair3", "date3", "title3", "score3", True)]
            await db.executemany('''
                        INSERT INTO POSTS(id, author, flair, created_utc, title, score, count_to_limit) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', posts)
            await db.commit()

        # when / then
        PostWithId = namedtuple("Post", "permalink")
        assert await testee.contains(PostWithId('perma1')) is True
        assert await testee.contains(PostWithId('perma7')) is False

