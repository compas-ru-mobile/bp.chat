
from bp_chat.logic.chat_api.BaseParser import BaseParser
from bp_chat.logic.chat_api.ChatApiCommon import tryable


class GetUsersAvatarParser(BaseParser):

    @tryable
    def onSuccess(self, json):
        if "result" in json:
            print('[ GetUsersAvatarParser ]')

            avatar_json = json["result"]
            self.parseUsersAvatars(avatar_json)

            self.chatApi.startLoadUsersAvatars()

            return True

        return False

    @tryable
    def parseUsersAvatars(self, json):
        print('[ GetUsersAvatarParser.parseUsersAvatars ]')
        if json == None:
            return

        for user_id, file_id in json.items():
            user = self.chatApi.users.get(str(user_id))
            if user:
                user.profile.setPhotoId(file_id)
