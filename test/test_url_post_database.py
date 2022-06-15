from collections import namedtuple
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio

from posts.url_post_repository import UrlPosts

test_db = f"some_url_post_test_db.db"


async def add_test_data(posts):
    async with aiosqlite.connect(test_db) as db:
        await db.executemany('''
                            INSERT INTO POSTS(id, author, flair, created_utc, score, count_to_limit, available) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''', posts)
        await db.commit()


def a_post(num):
    return f"id{num}", f"url{num}", \


class TestUrlPostDatabaseIntegration:

    @pytest_asyncio.fixture(autouse=True)
    async def before_each(self):
        # given
        Path(test_db).unlink(missing_ok=True)
        testee = UrlPosts(test_db)
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
                assert rows == ['URL_POSTS']

            async with db.execute("select sql from sqlite_master where type = 'table' and name = 'URL_POSTS';") as cursor:
                rows = [row[0] async for row in cursor]
                assert rows == [
                    'CREATE TABLE URL_POSTS (id PRIMARY KEY, url)']

    @pytest.mark.asyncio
    async def test_store(self):
        # given
        aPost = namedtuple("Post", "id url")
        store_posts = [aPost("id1", "url1"), aPost("id2", "url2"), aPost("id3", "url3"),]

        # when
        testee = UrlPosts(test_db)
        for p in store_posts:
            await testee.store(p)

        # then
        async with aiosqlite.connect(test_db) as db:
            async with db.execute("select * from URL_POSTS") as cursor:
                rows = [row async for row in cursor]
                assert len(rows) == 3
                assert a_post(1) in rows
                assert a_post(2) in rows
                assert a_post(3) in rows

    @pytest.mark.asyncio
    async def test_find_url(self):
        # given
        aPost = namedtuple("Post", "id url")
        store_posts = [aPost("id1", "url1"), aPost("id2", "url2"), aPost("id3", "url3"),]

        testee = UrlPosts(test_db)
        for p in store_posts:
            await testee.store(p)

        # when
        posts = await testee.fetch("url2")

        # then
        assert posts == ["id2"]


    @pytest.mark.asyncio
    async def test_remove(self):
        # given
        aPost = namedtuple("Post", "id url")
        store_posts = [aPost(f"id{i}", f"url{i}") for i in range(10)]

        testee = UrlPosts(test_db)
        for p in store_posts:
            await testee.store(p)

        # when
        await testee.remove(['id3', 'id6', 'id7', 'id8', 'id9'])

        # then
        async with aiosqlite.connect(test_db) as db:
            async with db.execute("select id from URL_POSTS") as cursor:
                rows = [row[0] async for row in cursor]
                assert rows == ['id0', 'id1', 'id2', 'id4', 'id5']

