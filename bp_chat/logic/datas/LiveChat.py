from .Chat import Chat


class LiveChat(Chat):

    LIVE_MINE = 16
    LIVE_TAKEN = 8

    LIVE_QUESTED = 3
    LIVE_OTHERS_OR_TAKEN = 2
    LIVE_ANSWERED = 1
    LIVE_CREATED_OR_FINISHED = 0

    guest_id = None
    guest_login = None

    def __init__(self, name, chat_id, guest_login=None, guest_id=None, cochat=-1):
        super().__init__(name, Chat.LIVE_CHAT, cochat=cochat)
        self.chat_id = chat_id
        self.guest_id = guest_id
        self.guest_login = guest_login

    def getName(self, full=True):
        if self.chat_api.isUserGuest():
            return "Support"
        return super().getName()

    def getIconName(self):
        return "live_chat_2"


    # FROM kivy version:
    # FIXME all statuses...
    _all_live_statuses = {0: '#54d554',  # green
                          1: '#ff4c4c',  # red
                          2: '#edaf42',  # yellow
                          3: '#bebebe',  # gray
                          4: '#ffffff'}  # white

    _live_status = -1

    def _get_live_status(self):
        return self._live_status

    def _set_live_status(self, status):
        if status < 0:
            return
        all = self._all_live_statuses
        self.round_background_color = all[status]
        self._live_status = status

    _live_manager = -1

    @property
    def live_manager(self):
        return self._live_manager

    @live_manager.setter
    def live_manager(self, value):
        # text = 'Manager {} completed your request'
        # if str(value) != '-1':
        #     nick = self.root.users.get(value, '') or self.root.users.get(str(value), '')
        #     self.completed_mess_text = text.format(nick)
        self._live_manager = value

    def get_live_state(self):
        last_mess_sender = self.last_message and self.last_message.getSender()
        if self.has_live_manager():
            if self.is_mine():
                if last_mess_sender:
                    if last_mess_sender.is_guest():
                        return self.LIVE_QUESTED
                    elif last_mess_sender.is_bot:
                        return self.LIVE_OTHERS_OR_TAKEN
                return self.LIVE_ANSWERED
            else:
                return self.LIVE_OTHERS_OR_TAKEN
        else:
            if last_mess_sender and last_mess_sender.is_guest():
                return self.LIVE_QUESTED
        return self.LIVE_CREATED_OR_FINISHED

        # if self.last_message:
        #     sender = self.last_message.getSender()
        #     if sender:
        #         is_bot = sender.is_bot
        #         is_guest = sender.is_guest()
        #         if is_guest:
        #             if self.has_live_manager() and not self.is_mine():
        #                 return self.LIVE_OTHERS
        #             return self.LIVE_QUESTED
        #         elif not is_bot:
        #             return self.LIVE_ANSWERED
        # return self.LIVE_CREATED_OR_FINISHED

    @property
    def chat_color(self):
        state = self.get_live_state()
        if state == self.LIVE_QUESTED:
            return "#f3958e" #"#f8685d" # RED
        elif state == self.LIVE_ANSWERED:
            return "#96cf5e" # GREEN
        elif state == self.LIVE_OTHERS_OR_TAKEN:
            return "#f8ed8a" #"#e8d424"  # YELLOW
        return "#cecbcb" #"#a7a7a7" # GREY

    @chat_color.setter
    def chat_color(self, value):
        pass

    def has_live_manager(self):
        return self.live_manager != -1

    def is_mine(self):
        return self.has_live_manager() and str(self.live_manager) == str(self.chat_api.getCurrentUserId())

    def live_manager_name(self):
        user = self.chatApi.users.get(self.live_manager, None)
        if user:
            return user.name

    def is_chat_muted(self):
        return not self.is_mine() and (
                self.has_live_manager() or
                self.get_live_state() not in (self.LIVE_QUESTED, self.LIVE_ANSWERED, self.LIVE_OTHERS_OR_TAKEN))
