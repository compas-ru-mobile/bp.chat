

def ChatApiCallback(method):
    _ChatApiCallbacksBase._abs_methods[method.__name__] = method
    return method


class _ChatApiCallbacksBase:
    _abs_methods = {}


class ChatApiCallbacksClean:

    def __init__(self, chat_api=None):
        self.chat_api = chat_api

    def __getattr__(self, item):
        if item == 'common_callback':
            return super().__getattribute__(item)
        return getattr(self, 'common_callback')

    def common_callback(self, *args, **kwargs):
        pass


class ChatApiCallbacks(_ChatApiCallbacksBase):

    def __init__(self):
        not_implemented = []
        for name, method in self._abs_methods.items():
            me = getattr(self.__class__, name)
            need_implement = method != me and me != None
            if not need_implement:
                not_implemented.append(name)
        if len(not_implemented) > 0:
            raise Exception("Not implemented ChatApi callbacks:\n\t{}".format("\n\t".join(not_implemented)))

    @ChatApiCallback
    def connectedCallback(self):
        pass

    @ChatApiCallback
    def disconnectedCallback(self):
        pass

    @ChatApiCallback
    def gotLoggedInCallback(self):
        pass

    @ChatApiCallback
    def gotConnectFinCallback(self):
        pass

    @ChatApiCallback
    def gotUsersListCallback(self, users):
        pass

    @ChatApiCallback
    def gotChatsListCallback(self, chats):
        pass

    @ChatApiCallback
    def chatOpenedCallback(self, openedChatId, withOpenChat):
        pass

    @ChatApiCallback
    def messagesUpdateCallback(self, withScrollToBottom):
        pass

    @ChatApiCallback
    def needRegisterCallback(self):
        pass

    @ChatApiCallback
    def needShowErrorCallback(self, error, message):
        pass

    @ChatApiCallback
    def chatsUpdatedListCallback(self):
        pass

    @ChatApiCallback
    def updateNavigationDrawerCallback(self):
        pass

    @ChatApiCallback
    def gotAvatarCallback(self):
        pass

    @ChatApiCallback
    def updateUserProfileCallback(self, user_id):
        pass

    @ChatApiCallback
    def changeUserTypeCallback(self, user_type):
        pass

    @ChatApiCallback
    def gotChatUsersCallback(self, users):
        pass

    @ChatApiCallback
    def fileProgressCallback(self, fileId, progress, download):
        pass

    @ChatApiCallback
    def closeResendWidget(self):
        pass

    @ChatApiCallback
    def needShowNotify(self, noti_text):
        pass

    @ChatApiCallback
    def needShowSmartInfo(self, smart_text):
        pass

    @ChatApiCallback
    def needApplyBadges(self, badgesCount):
        pass

    @ChatApiCallback
    def lastVersionGreater(self, ver):
        pass

    @ChatApiCallback
    def onNeedshowUpdateButton(self):
        pass

    @ChatApiCallback
    def onNewUpdateProgress(self, progress):
        pass

    @ChatApiCallback
    def onNeedCloseApp(self):
        pass

    @ChatApiCallback
    def gotServerSettings(self, d):
        pass

    @ChatApiCallback
    def gotServerInfo(self, d):
        pass

    @ChatApiCallback
    def needCloseAllOpenedWindows(self):
        pass

    @ChatApiCallback
    def onAdmInfo(self, d):
        pass

    @ChatApiCallback
    def needRaiseWindow(self):
        pass

    @ChatApiCallback
    def needShowChat(self, chat_id, chat_name):
        pass

    def onMessageCallback(self, message):
        pass

    @ChatApiCallback
    def onInputCall(self, text):
        pass

    @ChatApiCallback
    def needShowFindLine(self, val):
        pass
