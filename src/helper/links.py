
def permalink(item):
    return f"https://www.reddit.com{getattr(item, 'permalink', item)}"
