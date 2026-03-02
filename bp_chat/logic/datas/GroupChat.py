
from .Chat import Chat


class GroupChat(Chat):

    def __init__(self, name, chat_id, cochat=-1):
        super().__init__(name, Chat.GROUP_CHAT, cochat=cochat)
        self.chat_id = chat_id

    def getIconName(self):
        return "group"

