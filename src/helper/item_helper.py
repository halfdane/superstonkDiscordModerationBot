import re

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


emoj = re.compile("["
                  u"\U0001F600-\U0001F64F"  # emoticons
                  u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                  u"\U0001F680-\U0001F6FF"  # transport & map symbols
                  u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                  u"\U00002500-\U00002BEF"  # chinese char
                  u"\U00002702-\U000027B0"
                  u"\U00002702-\U000027B0"
                  u"\U000024C2-\U0001F251"
                  u"\U0001f926-\U0001f937"
                  u"\U00010000-\U0010ffff"
                  u"\u2640-\u2642"
                  u"\u2600-\u2B55"
                  u"\u200d"
                  u"\u23cf"
                  u"\u23e9"
                  u"\u231a"
                  u"\ufe0f"  # dingbats
                  u"\u3030"
                  "]+", re.UNICODE)


def remove_emojis(text_with_emojis):
    return emoj.sub('', text_with_emojis)