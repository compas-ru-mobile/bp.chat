

class CurrentChatMessages:

    def __init__(self):
        self.messages = {}
        self.messages_list = []
        self.first_id = -1
        self.last_id = -1

    def count(self):
        return len(self.messages)

    def insert(self, key, message):
        self.messages[key] = message
        messages_list = sorted(self.messages.values(), key=lambda mess: int(mess.mes_id))
        first_id, last_id = messages_list[0].mes_id, messages_list[-1].mes_id

        self.keys = sorted(self.messages.keys())
        self.messages_list, self.first_id, self.last_id = messages_list, first_id, last_id

    def get_messages(self):
        return self.messages_list

    def get_messages_dict(self):
        return self.messages

    def get_first_id(self):
        if len(self.messages_list) > 0:
            return self.messages_list[0].mes_id
