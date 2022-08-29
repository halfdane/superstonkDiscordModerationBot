from helper.item_helper import author


async def get_qv_comment(qvbot_reddit, post):
    qv_user = await qvbot_reddit.user.me()
    if len(post.comments) > 0 and post.comments[0].stickied and author(post.comments[0]) == qv_user.name:
        return await qvbot_reddit.comment(id=post.comments[0].id)

    return None