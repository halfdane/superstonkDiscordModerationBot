from disnake.utils import escape_markdown


def permalink(item):

    return f"https://new.reddit.com{getattr(item, 'permalink', getattr(item, 'target_permalink', '/'+str(item)))}"

def user_page(redditor):
    return f"https://new.reddit.com/u/{redditor}"

def make_safe(maybe_string):
    string = str(maybe_string)
    clipped = str(string[:100])
    clipped += '...' if len(string) > 100 else ''
    return escape_markdown(clipped).replace('\n', ' ')

def removed(item):
    submission_removed = getattr(item, 'removed_by_category', None) is not None
    comment_deleted = getattr(item, 'body', '') == '[deleted]'
    comment_removed = getattr(item, 'removed', False)
    comment_author_banned = getattr(item, "ban_note", None) is not None

    return submission_removed or comment_deleted or comment_removed or comment_author_banned