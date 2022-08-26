from collections import namedtuple

from helper.item_helper import permalink


class TestPermalinks:

    def test_item_permalink(self):
        # given
        thing_with_permalink = namedtuple("Post", "id permalink")

        # when
        link = permalink(
            thing_with_permalink("an_id", "/r/Superstonk/comments/vlk8rp/just_passed_800000_members/idwn2or/"))

        # then
        assert link == "https://new.reddit.com/r/Superstonk/comments/vlk8rp/just_passed_800000_members/idwn2or/"

    def test_id_permalink(self):
        # given

        # when
        link = permalink("vlk8rp")

        # then
        assert link == "https://new.reddit.com/vlk8rp"

    def test_modaction_permalink(self):
        # given
        thing_with_target_permalink = namedtuple("Post", "id target_permalink")

        # when
        link = permalink(
            thing_with_target_permalink("an_id", "/r/Superstonk/comments/vlk8rp/just_passed_800000_members/idwn2or/"))

        # then
        assert link == "https://new.reddit.com/r/Superstonk/comments/vlk8rp/just_passed_800000_members/idwn2or/"



