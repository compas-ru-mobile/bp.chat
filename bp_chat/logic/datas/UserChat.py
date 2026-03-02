from .Chat import Chat
from bp_chat.core.tryable import ConsoleThread

class UserChat(Chat):

    user = None

    def __init__(self, user):
        super().__init__(None, Chat.PRIVATE_CHAT)
        self.user = user

    def getLogin(self):
        name = self.user.login
        name = self.user.fix_name(name)
        return name

    def getNameByProfile(self):
        if self.is_private():
            if self.user and self.user.profile:
                return self.user.profile.getFullName()
        return ''

    def getName(self, full=True):
        add = ""
        if self.chat_api.is_admin:
            add += " #{}".format(self.user.id)
        if str(self.chat_api.getCurrentUserId()) == str(self.user.id):
            add += " (you)"

        name = self.getLogin()
        name_full = name + add

        # if full:
        #     name2 = self.getNameByProfile()
        #     if name2 and name2 != name:
        #         name_full += " " + name2

        return name_full # self.user.name

    def getIconName(self):
        return "user"

    def getAvatar(self):
        return self.user.profile.getBitmap()
