from datetime import datetime
import logging
import disnake

DEVELOP_ROLES = {
    "goldfish": 1034001950326390784,
    "limited": 1034002119465914460,
    "general": 1034002358306340925,
    "admin": 1034006933146968064
}

PRODUCTION_ROLES = {
    "goldfish": 887026874675519548,
    "limited": 943655369715109948,
    "general": 829007921555046461,
    "admin": 829007443584483368

}


class DiscordUserInfo:

    def __init__(self, report_channel, is_live_environment, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.report_channel = report_channel
        if is_live_environment:
            self.roles = PRODUCTION_ROLES
        else:
            self.roles = DEVELOP_ROLES

    def wot_doing(self):
        return "Fetch user info about discord members"

    def is_goldfish(self, user_name):
        return self.has_role(user_name, "goldfish")

    def is_limited(self, user_name):
        return self.has_role(user_name, "limited")

    def is_general(self, user_name):
        return self.has_role(user_name, "general")

    def is_admin(self, user_name):
        return self.has_role(user_name, "admin")

    def is_moderator(self, user_name):
        return self.is_goldfish(user_name) or self.is_limited(user_name) or self.is_general(user_name) or self.is_admin(
            user_name)

    def has_role(self, user_name, role_name):
        member = disnake.utils.get(self.report_channel.guild.members, name=user_name)
        role = disnake.utils.get(member.roles, id=self.roles[role_name])
        return role is not None
