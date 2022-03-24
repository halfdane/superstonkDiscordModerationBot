import disnake

from redditItemHandler import Handler


class ModMail(Handler):

    def _get_reddit_stream_function(self, subreddit):
        return subreddit.modmail.conversations

    async def create_embed(self, item):
        url = f"https://mod.reddit.com/mail/all/{item.id}"
        e = disnake.Embed(
            url=url,
            colour=disnake.Colour(0).from_rgb(207, 206, 255))
        e.description = f"""[Highlighed modmail conversation: '{item.conversation.subject}']({url})"""
        return e
