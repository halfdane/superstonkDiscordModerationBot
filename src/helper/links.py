from disnake.utils import escape_markdown


def permalink(item):
    return f"https://www.reddit.com{getattr(item, 'permalink', item)}"


def make_safe(maybe_string):
    string = str(maybe_string)
    clipped = str(string[:50])
    clipped += '...' if len(string) > 50 else ''
    return escape_markdown(clipped).replace('\n', ' ')