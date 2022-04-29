from datetime import datetime, timedelta

from cachetools import TTLCache

from redditItemHandler import Handler

from disnake import Embed
import disnake


class PostCountLimiter(Handler):
    _restricted_interval = {"hours": 24}

    def __init__(self, bot):
        super().__init__(bot)
        self.cache = TTLCache(maxsize=1000, ttl=timedelta(**self._restricted_interval), timer=self.timer_function)
        self.timestamp_to_use = None

    def timer_function(self):
        if self.timestamp_to_use is not None:
            return self.timestamp_to_use
        else:
            return datetime.now()

    async def on_ready(self):
        await self.initial_cache_population()

    async def initial_cache_population(self):
        async for post in self.bot.subreddit.top(time_filter="day", limit=None):
            utc_dt = datetime.utcfromtimestamp(post.created_utc)
            self.timestamp_to_use = utc_dt
            await self.take(post)

        self.timestamp_to_use = None

        for author, posts in self.cache.items():
            await self.report_infraction(author, posts)

    async def take(self, item):
        self.cache.expire()
        posts = self.cache.get(item.author.name,
                               TTLCache(maxsize=10, ttl=timedelta(**self._restricted_interval), timer=self.timer_function))
        posts.expire()
        posts[item.id] = {
            'permalink': self.permalink(item),
            'created_utc': datetime.utcfromtimestamp(item.created_utc)
        }
        self.cache[item.author.name] = posts
        await self.report_infraction(item.author, posts)

    async def report_infraction(self, author, posts):
        if self.timestamp_to_use is None and len(posts) > 5:
            self._logger.info(f"Oops, looks like {author} is posting a lot: {posts}")

            embed = Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))
            embed.description = f"** {author} posted more than 5 posts in the last 24 hours:**"

            count = 0
            for v in sorted(posts.values(), key=lambda x: x['created_utc']):
                count += 1
                embed.add_field(v['created_utc'], v['permalink'], inline=False)

                if count % 20 == 0:
                    await self.bot.report_channel.send(embed=embed)
                    embed = disnake.Embed(colour=disnake.Colour(0).from_rgb(207, 206, 255))

            if count % 20 != 0:
                embed.add_field("Redditor", f"[{author}](https://www.reddit.com/u/{author})", inline=False)
                msg = await self.bot.report_channel.send(embed=embed)
                await self.bot.add_reactions(msg)

