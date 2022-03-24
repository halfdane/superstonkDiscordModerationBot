import disnake

from helper.discord_text_formatter import link, cut
from redditItemHandler import Handler


class Reports(Handler):
    def _get_reddit_stream_function(self, subreddit):
        return subreddit.mod.stream.reports

    def should_handle(self, item):
        user_report_count = sum([r[1] for r in item.user_reports])
        mod_report_count = len(list(filter(lambda r: r[1] != "AutoModerator", item.mod_reports)))
        return user_report_count >= 5 or mod_report_count > 0

    async def create_embed(self, item):
        url = f"https://www.reddit.com{item.permalink}"
        e = disnake.Embed(
            url=url,
            colour=disnake.Colour(0).from_rgb(207, 206, 255))

        title = getattr(item, 'title', getattr(item, 'body', ""))[:75]
        e.description = f"[Reported {item.__class__.__name__}: {title}]({url})"
        e.add_field("Redditor", link(f"https://www.reddit.com/u/{item.author}", item.author), inline=False)

        user_reports = "\n".join(f"{r[1]} {r[0]}" for r in item.user_reports)
        if user_reports:
            e.add_field("User Reports", user_reports, inline=False)

        mod_reports = "\n".join(f"{r[1]} {r[0]}" for r in item.mod_reports)
        if mod_reports:
            e.add_field("Mod Reports", mod_reports, inline=False)
        return e
