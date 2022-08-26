from disnake.utils import escape_markdown
from asyncpraw.models.reddit.modmail import ModmailConversation


def permalink(item):
    if hasattr(item, 'permalink'):
        return f"https://new.reddit.com{item.permalink}"
    elif hasattr(item, 'target_permalink'):
        return f"https://new.reddit.com{item.target_permalink}"
    elif isinstance(item, ModmailConversation):
        return f"https://mod.reddit.com/mail/all/{item.id}"
    else:
        return f"https://new.reddit.com/{str(item)}"


def user_page(redditor):
    return f"https://www.reddit.com/u/{redditor}"


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


def author(item):
    author_attr = getattr(item, 'author', getattr(item, 'participant', None))
    return getattr(author_attr, 'name', author_attr)

