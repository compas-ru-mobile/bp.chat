
import traceback, sys
import traceback, sys
# try:
#     from colorama import init
#     from termcolor import colored
#     init()
# except ImportError:
colored = lambda s, *args: s
from datetime import datetime

from .BaseParser import BaseParser
from .UpdateParser import UpdateParser
from ..datas.Message import Message
from . import ChatApiCommon
from .ChatApiCommon import tryable

from ...logic.chat_api.DeliveredSender import DeliveredSender


class CommonDataParser(BaseParser):

    __updateParser = None

    def getUpdateParser(self):
        if self.__updateParser == None:
            self.__updateParser = UpdateParser()
        return self.__updateParser

    @tryable
    def onSuccess(self, json):
        if "result" in json:
            #new_messages = {}

            _update_with_scroll_to_bottom = True
            if self.chatApi._getting_last_messages and self.chatApi.current_chat_id == self.chatApi._getting_last_messages['chat_id']:
                _update_with_scroll_to_bottom = False

            result = json["result"]
            if self.is_message(result) and "messages" in result:

                messages = result.get("messages")
                by = result.get('by')

                self.chatApi.logger.info("got {} messages".format(len(messages)))
                self.debug("    << GOT messages >> : " + str(len(messages)))

                i = 0
                chats_changed = False
                chatOpened = -1

                noti_text = None
                noti_chat_id = -1
                noti_key = None

                if len(messages) == 0:
                    # FIXME: HACK !!!
                    if self.chatApi.getOpeningChatId() >= 0:
                        chatOpened = self.setChatOpened()

                deliveredSender = DeliveredSender.getInstance()

                for key, messageJson in messages.items():
                    i += 1
                    try:
                        message = Message.fromJSONObject(messageJson)
                        message.mes_id = int(key)

                        if not message.getDelivered():
                            deliveredSender.add(message.chat_id, message.mes_id)

                        #new_messages[key] = message

                        if message.api_type == 'INPUT_CALL':
                            if self.chatApi.callbacks != None and by != 'api':
                                self.chatApi.callbacks.onInputCall(message.api_kwargs['from'])

                        self.chatApi.saveLastMessageForChatsWhenOpens(message)
                        chats_changed |= self.chatApi.fillChatsFromSavedLastMessages()

                        current_user_id = self.chatApi.getCurrentUserId()

                        if self.chatApi.getCurrentChatId() == -1 and self.chatApi.getOpeningChatId() >= 0 and message.chat_id == self.chatApi.getOpeningChatId():
                            chatOpened = self.setChatOpened()
                        else:
                            chatOpened = self.chatApi.getCurrentChatId()

                        may_notify = False
                        chat = self.chatApi.getChatById(message.chat_id)
                        muted = chat and chat.is_chat_muted()

                        if not message.getDelivered() or self.chatApi.need_my_messages:
                            if message.sender_id != current_user_id or self.chatApi.need_my_messages:
                                if chatOpened < 0 or chatOpened != message.chat_id or not self.chatApi.isGuiVisible():
                                    if muted:
                                        pass
                                    else:
                                        may_notify = True
                                    self.chatApi.addBadgesToChat(message.chat_id, 1, cause="from_server")

                                if self.chatApi.callbacks != None:
                                    self.chatApi.callbacks.onMessageCallback(message)

                        if message.chat_id == self.chatApi.getCurrentChatId():
                            if self.chatApi.isGuiVisible():
                                may_notify = False
                            self.chatApi.insertMessage_to_currentChat(key, message)
                            #self.chatApi.current_chat_messages.insert(key, message)

                        if may_notify:
                            noti_sender = str(message.getSenderName()) + ": "
                            noti_text = ""

                            noti_text += message.text.replace('<b>', '').replace('</b>', '')

                            if len(noti_text) == 0 and message.quote != None:
                                noti_text = message.quote.message

                            noti_text = noti_sender + noti_text
                            noti_chat_id = message.chat_id
                            noti_key = key

                    except Exception as e:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        fexc = traceback.format_exception(exc_type, exc_value,
                                                          exc_traceback)
                        fe_line = ''.join(fexc[2:])
                        if not ', line' in fe_line:
                            fe_line = ''.join(fexc)

                if noti_text != None:
                    if self.chatApi.getCurrentOrOpeningChatId() != noti_chat_id or not self.chatApi.isGuiVisible():
                        noti_title = self.chatApi.getChatName(noti_chat_id, full=False) or ""
                        ChatApiCommon.doNotify(noti_text, noti_title)#, noti_chat_id, noti_key, self.chatApi.getChatsWithBadgesCount())

                if self.chatApi.callbacks != None:
                    self.chatApi.callbacks.messagesUpdateCallback(_update_with_scroll_to_bottom)

                if chats_changed:
                    pass

                return True

            elif self.is_update(result):

                return self.getUpdateParser().onSuccess(result)

        return False

    def setChatOpened(self):
        return self.chatApi.setChatOpened()
        # chatOpened = self.chatApi.getOpeningChatId()
        # self.chatApi.setCurrentChatId(chatOpened)
        # self.chatApi.setOpeningChatId(-1)
        # self.chatApi.setLastChatOpenedTime(datetime.now())
        # if self.chatApi.callbacks != None:
        #     self.chatApi.callbacks.chatOpenedCallback(chatOpened, False)
        # return chatOpened

