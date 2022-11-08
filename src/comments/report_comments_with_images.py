from reddit_item_handler import Handler


class ReportCommentsWithImages(Handler):

    def __init__(self, **kwargs):
        super().__init__()

    def wot_doing(self):
        return "Remove images that aren't in the Meme Competition"

    async def take(self, item):
        if getattr(item, "media_metadata", []) and len(item.media_metadata) > 0:
            await item.report("Comment with image")


