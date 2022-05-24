from collections import namedtuple
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio

from posts.post_repository import Posts

test_db = f"some_post_test_db.db"


def a_post(num, id=None, author=None, flair=None, created=None, title=None, score=None, counts=None):
    return id if id else f"id{num}", \
           author if author else f"auth{num}", \
           flair if flair else f"flair{num}", \
           created if created else f"date{num}", \
           title if title else f"title{num}", \
           score if score else f"score{num}", \
           counts if counts else f"cnt{num}",


async def add_test_data(posts):
    async with aiosqlite.connect(test_db) as db:
        await db.executemany('''
                            INSERT INTO POSTS(id, author, flair, created_utc, title, score, count_to_limit) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''', posts)
        await db.commit()


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
        PostWithLimit = namedtuple("Post", "id author link_flair_text created_utc title score count_to_limit")
        PostWithoutLimit = namedtuple("Post", "id author link_flair_text created_utc title score")

        store_posts = [
            PostWithLimit("id1", Author("auth1"), "flair1", "date1", "title1", "score1", "cnt1"),
            PostWithoutLimit("id2", Author("auth2"), "flair2", "date2", "title2", "score2"),
            PostWithLimit("id3", Author("auth3"), "flair3", "date3", "title3", "score3", "cnt3"),
        ]

        # when
        testee = Posts(test_db)
        await testee.store(store_posts)

        # then
        async with aiosqlite.connect(test_db) as db:
            async with db.execute("select * from POSTS") as cursor:
                rows = [row async for row in cursor]
                assert len(rows) == 3
                assert a_post(1) in rows
                assert a_post(2, counts=True) in rows
                assert a_post(3) in rows

    @pytest.mark.asyncio
    async def test_read_all(self):
        # given
        await add_test_data([a_post(1), a_post(2), a_post(3)])

        # when
        testee = Posts(test_db)
        posts = await testee.fetch()

        # then
        assert len(posts) == 3
        for i in range(3):
            assert posts[i].id == f"id{i + 1}"
            assert posts[i].author.name == f"auth{i + 1}"
            assert posts[i].link_flair_text == f"flair{i + 1}"
            assert posts[i].created_utc == f"date{i + 1}"
            assert posts[i].title == f"title{i + 1}"
            assert posts[i].score == f"score{i + 1}"
            assert posts[i].count_to_limit == f"cnt{i + 1}"

    @pytest.mark.asyncio
    async def test_read_from_user(self):
        # given
        await add_test_data([a_post(1, author='auth1'),
                             a_post(2),
                             a_post(3, author='auth1')])

        # when
        testee = Posts(test_db)
        posts = await testee.fetch(author="auth1")

        # then
        assert len(posts) == 2
        assert posts[0].id == f"id1"
        assert posts[0].author.name == f"auth1"

        assert posts[1].id == f"id3"
        assert posts[1].author.name == f"auth1"

    @pytest.mark.asyncio
    async def test_read_after(self):
        # given
        now = datetime.utcnow()
        last_week = now - timedelta(weeks=1)
        three_days_ago = now - timedelta(days=3)
        two_days_ago = now - timedelta(days=2)

        await add_test_data([a_post(1, created=three_days_ago.timestamp()),
                             a_post(2, created=last_week.timestamp(), id='old'),
                             a_post(3, created=two_days_ago.timestamp())])

        # when
        four_days_ago = now - timedelta(days=4)
        testee = Posts(test_db)
        posts = await testee.fetch(since=four_days_ago)

        # then
        assert len(posts) == 2
        assert posts[0].id == f"id1"
        assert posts[1].id == f"id3"

    @pytest.mark.asyncio
    async def test_read_counting_only(self):
        # given
        await add_test_data([a_post(1, counts=True),
                             a_post(2, counts=False),
                             a_post(3, counts=False),
                             a_post(4, counts=True)])

        # when
        testee = Posts(test_db)
        posts = await testee.fetch(only_counting_to_limit=True)

        # then
        assert len(posts) == 2
        assert posts[0].id == f"id1"
        assert posts[1].id == f"id4"

    @pytest.mark.asyncio
    async def test_read_author_after(self):
        # given
        now = datetime.utcnow()
        last_week = now - timedelta(weeks=1)
        three_days_ago = now - timedelta(days=3)
        two_days_ago = now - timedelta(days=2)

        await add_test_data([a_post(1, created=three_days_ago.timestamp()),
                             a_post(2, created=last_week.timestamp(), id='old'),
                             a_post(3, created=two_days_ago.timestamp())])

        # when
        four_days_ago = now - timedelta(days=4)
        testee = Posts(test_db)
        posts = await testee.fetch(since=four_days_ago, author='auth3')

        # then
        assert len(posts) == 1
        assert posts[0].id == f"id3"

    @pytest.mark.asyncio
    async def test_do_not_count(self):
        # given
        testee = Posts(test_db)
        await add_test_data([a_post(1, counts=True),
                             a_post(2, counts=False),
                             a_post(3, counts=True),
                             a_post(4, counts=True)])

        posts = await testee.fetch(only_counting_to_limit=True)
        assert len(posts) == 3
        assert posts[0].id == f"id1"
        assert posts[1].id == f"id3"
        assert posts[2].id == f"id4"

        # when
        PostWithId = namedtuple("Post", "id")

        await testee.do_not_count_to_limit(PostWithId('id1'))

        # then
        posts = await testee.fetch(only_counting_to_limit=True)
        assert len(posts) == 2
        assert posts[0].id == f"id3"
        assert posts[1].id == f"id4"

    @pytest.mark.asyncio
    async def test_database_contains(self):
        # given
        testee = Posts(test_db)
        await add_test_data([a_post(1, counts=True),
                             a_post(2, counts=False),
                             a_post(3, counts=True),
                             a_post(4, counts=True)])

        # when / then
        PostWithId = namedtuple("Post", "id")
        assert await testee.contains(PostWithId('id1')) is True
        assert await testee.contains(PostWithId('id7')) is False
