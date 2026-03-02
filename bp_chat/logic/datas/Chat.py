
from ..chat_api.api_object import ApiObject


class Chat(ApiObject):

    PRIVATE = 0
    GROUP = 1

    PRIVATE_CHAT = 0
    GROUP_CHAT = 1
    LIVE_CHAT = 2

    BADGES_NO = 0
    BADGES_HAS_MUTED = 1
    BADGES_HAS = 2

    name = None
    type = None
    chat_id = -1
    cochat = -1

    badges_count = 0
    last_message = None

    chat_color = None

    marked_last = 0

    def __init__(self, name, type, cochat=-1):
        self.name = name
        self.type = type
        self.cochat = cochat

    @property
    def id(self):
        return self.chat_id

    @property
    def title(self):
        return self.getName()

    def getLogin(self):
        return ''

    def getName(self, full=True):
        return self.name

    def getIconName(self):
        return None

    def set_name(self, name):
        self.name = name

    def is_private(self):
        return self.type == Chat.PRIVATE_CHAT

    def is_group(self):
        return self.type == Chat.GROUP_CHAT

    def is_live(self):
        return self.type == Chat.LIVE_CHAT

    def set_cochat(self, cochat):
        self.cochat = cochat

    def last_message_time_to_long(self):
        if self.last_message and self.last_message._time:
            return self.last_message._time.timestamp()
        return 0

    def getAvatar(self):
        return None

    def get_badges_count(self, is_filtered_by_last_readed=lambda boo:None):
        return self.badges_count

    def get_badges_state(self):
        if self.badges_count == 0:
            return self.BADGES_NO
        if self.is_chat_muted():
            return self.BADGES_HAS_MUTED
        return self.BADGES_HAS

    def get_last_message(self):
        return self.last_message

    def is_selected_chat(self):
        from bp_chat.logic.chat_api.ChatApi import ChatApi
        return self.id >= 0 and ChatApi.instance().getCurrentChatId() == self.id

    def is_chat_muted(self):
        return self.chat_api.is_chat_muted(self.chat_id)
