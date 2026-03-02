
from bp_chat.logic.chat_api.BaseParser import BaseParser
from bp_chat.logic.chat_api.ChatApiCommon import tryable


class GetUsersListParser(BaseParser):

    @tryable
    def onSuccess(self, json):
        if "result" in json:
            print('[ GetUsersListParser ]')
            self.parseUsersJson(json["result"])

            if self.chatApi.with_groups:
                self.chatApi.send(url="/group/", attrs={})

            if self.chatApi.with_avatars:
                self.chatApi.getUsersAvatars()

            return True

        return False

    @tryable
    def parseUsersJson(self, json):
        print('[ GetUsersListParser.parseUsersJson ]')
        self.chatApi.users = {}
        self.chatApi.chats[:] = []

        if json == None:
            return

        self.debug("[ GOT  ] users")

        for key, userJson in json.items():
            if "nick" in userJson:
                nick = userJson["nick"]
                status = userJson["status"]
                user_type = userJson["user_type"]
                is_bot = userJson.get("bot", False)

                if str(key) == str(self.chatApi.getCurrentUserId()):
                    self.chatApi.user_type = user_type
                    # FIXME on start it is not needed...

                self.chatApi.createUser(nick, key, status, user_type, is_bot)

        if self.chatApi.callbacks:
            self.chatApi.callbacks.gotUsersListCallback(self.chatApi.users)
