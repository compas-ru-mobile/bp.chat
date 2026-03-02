from time import sleep

from .api_object import ApiObject
from .ChatApiCommon import tryable, in_thread
from bp_chat.core.local_db_messages import LocalDbMessagesMap


class DeliveredSender(ApiObject):

    # // FIXME 2. добавить в общий поток отправки данных (создать этот поток в том числе)

    scheduleTaskExecutor = None
    scheduleTaskExecutor__stop = False


    @staticmethod
    def getInstance():
        return ApiObject.get_chat_api().getDeliveredSender(DeliveredSender)

    def __init__(self):
        self.delivered = {}
        self.delivered_by_gui = set()
        self.start()

    def start(self):
        if not self.scheduleTaskExecutor:
            self.scheduleTaskExecutor = True
            self._start_thread()

    @in_thread
    def _start_thread(self):
        while not self.scheduleTaskExecutor__stop:
            self._work()
            sleep(2)

    @tryable
    def _work(self):
        temp_delivered = list(self.delivered_by_gui)

        if len(temp_delivered) > 0 and self.chat_api.isGuiVisible():
            json = temp_delivered

            self.chat_api.send(url="/message/delivered/", attrs={"method": "POST", "delivered": json})
            self.delivered_by_gui.clear()

    def add_by_gui(self, id):
        if self.chat_api.isGuiVisible():
            self.delivered_by_gui.add(id)

    def add(self, chat_id, id):
        need = self.chat_api.isGuiVisible()
        chat_id = int(chat_id)

        self_delivered = self.delivered.get(chat_id)
        if not self_delivered:
            self_delivered = []

        tmp_delivered = set(self_delivered)
        tmp_delivered.add(id)
        self.delivered[chat_id] = list(tmp_delivered)

    def difference(self, json_obj):
        chatApi = self.chat_api

        count_badges = 0
        self_delivered_d = {}
        for chat_id, delivered in json_obj.items():
            chat_id = int(chat_id)

            for id in delivered:
                LocalDbMessagesMap.set_message_delivered(id, chatApi.server_uid, True)

            if chat_id == int(chatApi.getCurrentChatId()):
                self.setReadedForMessage(delivered)
                if chatApi.callbacks != None:
                    chatApi.callbacks.messagesUpdateCallback(False) # FIXME -- update --

            self_delivered = self.delivered.get(chat_id)
            if not self_delivered:
                self_delivered = []
            badges = len(set(self_delivered) & set(delivered))

            chatApi.addBadgesToChat(chat_id, -badges, cause="from_delivered")
            count_badges += badges

            total_delivered = self_delivered_d.get(chat_id)
            if not total_delivered:
                total_delivered = set()
            total_delivered = total_delivered | set(delivered)
            self_delivered_d[chat_id] = total_delivered

        for chat_id, total_delivered in self_delivered_d.items():
            chat_id = int(chat_id)
            self_delivered = self.delivered.get(chat_id)
            if not self_delivered:
                self_delivered = []
            self_delivered = list(set(self_delivered) - total_delivered)
            self.delivered[chat_id] = self_delivered

        chatApi.addBadges(-count_badges)

    def setReadedForMessage(self, messages):
        mData = self.chat_api.current_chat_messages.get_messages_dict()
        for id in messages:
            mes_to_change = mData.get(int(id), None)
            if mes_to_change:
                mes_to_change.setDelivered(True)

    def shutdown(self):
        self.scheduleTaskExecutor__stop = True
