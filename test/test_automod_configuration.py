import re
from collections import namedtuple

from automod_configuration import AutomodConfiguration
from helper.links import permalink


class TestAutomodConfiguration:

    def test_nothing_forbidden_with_empty_checks(self):
        # given
        automod = AutomodConfiguration(None, [], [])

        # when
        is_forbidden = automod.is_forbidden_user_message("this is a harmless string")

        # then
        assert is_forbidden is False

    def test_nothing_forbidden_with_regex_check(self):
        # given
        pattern = re.compile('lala')
        automod = AutomodConfiguration(None, [pattern], [])

        # when
        is_forbidden = automod.is_forbidden_user_message("this is a harmless string")

        # then
        assert is_forbidden is False

    def test_nothing_forbidden_with_domain_check(self):
        # given
        domain = "a_random_domain"
        automod = AutomodConfiguration(None, [], [domain])

        # when
        is_forbidden = automod.is_forbidden_user_message("this is a harmless string")

        # then
        assert is_forbidden is False


    def test_something_forbidden_with_regex_check(self):
        # given
        pattern = re.compile('la.a')
        automod = AutomodConfiguration(None, [pattern], [])

        # when
        is_forbidden = automod.is_forbidden_user_message("this is a lasa string")

        # then
        assert is_forbidden is True

    def test_something_forbidden_with_domain_check(self):
        # given
        domain = "a_random_domain"
        automod = AutomodConfiguration(None, [], [domain])

        # when
        is_forbidden = automod.is_forbidden_user_message("this is a string with a_random_domain")

        # then
        assert is_forbidden is True

    def test_something_forbidden_with_both_check(self):
        # given
        pattern = re.compile('la.a')
        domain = "a_random_domain"
        automod = AutomodConfiguration(None, [pattern], [domain])

        # when
        # then
        assert automod.is_forbidden_user_message("this is a lasa string") is True
        assert automod.is_forbidden_user_message("this is a harmless string with a_random_domain") is True
