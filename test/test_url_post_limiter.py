from posts.post_url_limiter import UrlPostLimiter


class TestUrlPostLimiter:
    def test_stem_twitter_url(self):
        # given
        urls = ["https://twitter.com/pulte/status/1540350871036637184?s=21&t=aWXd9ZtQhnnn-C_ebMCZig",
                "https://twitter.com/pulte/status/1540350871036637184?s=21&t=P0sCd__yXjSiT1cTW_ECUA"]

        tweet_url = "https://twitter.com/pulte/status/1540350871036637184"

        testee = UrlPostLimiter(post_repo=None, url_post_repo=None,
                                qvbot_reddit=None,
                                is_live_environment=None, quality_vote_bot_configuration=None,
                                send_discord_message=None,
                                superstonk_moderators=None)

        # when
        for url in urls:
            actual_tweet = testee.reduce_url(url)
            assert actual_tweet == tweet_url
