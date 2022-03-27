from asyncpraw.models.reddit.redditor import Redditor
from pprint import pprint, pformat


class BagOfStuff:
    def __init__(self, **attributes):
        for param, value in attributes.items():
            self.__setattr__(param, value)

    def __repr__(self):
        return pformat(vars(self))


class RedditorResearch(BagOfStuff):
    pass


class Activity(BagOfStuff):
    pass


class Activities(BagOfStuff):
    pass


async def redditor_history(redditor: Redditor):
    try:
        return await __unsafe_redditor_history(redditor)
    except Exception as e:
        return {
            "Redditor": f"[{redditor.name}](https://www.reddit.com/u/{redditor.name})",
            "ERROR": f"Couldn't fetch the history: {e}\n"
                     f"You'll have to check it yourself."
        }


async def __unsafe_redditor_history(redditor):
    submissions = await history_of(redditor.submissions.new())
    comments = await history_of(redditor.comments.new())
    return {
        "Redditor": f"[{redditor.name}](https://www.reddit.com/u/{redditor.name})",
        f"Additional Links":
            f"[Camas for {redditor.name}](https://camas.github.io/reddit-search/#%7B%22author%22:%22{redditor.name}%22,%22subreddit%22:%22Superstonk%22,%22resultSize%22:4500%7D)\n"
            f"[Modmail for {redditor.name}](https://mod.reddit.com/mail/search?q={redditor.name})",
        f"Submissions: {submissions.total_count} / {submissions.total_karma} karma":
            "\n".join(
                [f"**{a.subreddit}**: {a.count} ({a.count_percentage}%) / {a.karma} karma ({a.karma_percentage}%)"
                 for a in submissions.activities]),
        f"Comments: {comments.total_count} / {comments.total_karma} ":
            "\n".join(
                [f"**{a.subreddit}**: {a.count} ({a.count_percentage}%) / {a.karma} karma ({a.karma_percentage}%)"
                 for a in comments.activities])
    }


def add_percentages(total_count, total_karma):
    def calc(activity):
        activity.count_percentage = round(activity.count / total_count * 100)
        activity.karma_percentage = round(activity.karma / total_karma * 100)
        return activity

    return calc


async def history_of(listing):
    submissions = {}
    total_count = 0
    total_karma = 0
    async for n in listing:
        subreddit_name = n.subreddit.display_name
        values = submissions.get(subreddit_name, Activity(subreddit=subreddit_name, count=0, karma=0))
        values.count += 1
        values.karma += n.score
        total_count += 1
        total_karma += n.score
        submissions[subreddit_name] = values
    submissions = sorted(submissions.values(), key=lambda x: x.count, reverse=True)
    calc = add_percentages(total_count, total_karma)
    submissions = list(map(calc, submissions[:3]))
    return Activities(activities=submissions, total_count=total_count, total_karma=total_karma)
