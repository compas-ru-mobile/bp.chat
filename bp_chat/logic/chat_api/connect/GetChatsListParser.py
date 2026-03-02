
from datetime import datetime

from bp_chat.logic.chat_api.BaseParser import BaseParser
from bp_chat.logic.datas.GroupChat import GroupChat
from bp_chat.logic.datas.LiveChat import LiveChat
from bp_chat.logic.datas.Message import Message
from bp_chat.logic.chat_api.ChatApiCommon import tryable
from bp_chat.logic.chat_api import ChatApiCommon


class GetChatsListParser(BaseParser):

    @tryable
    def onSuccess(self, json):

        if "result" in json:
            print('[ GetChatsListParser ]')

            self.parserGroupsJson(json["result"])

            # FIXME
            self.chatApi.getUserProfile(self.chatApi.getCurrentUserId())

            if self.chatApi.is_admin:
                self.chatApi.send(url='/server/info/', attrs={})

            if self.chatApi.callbacks:
                self.chatApi.callbacks.gotConnectFinCallback()

            return True

        return False

    @tryable
    def parserGroupsJson(self, json):
        print('[ GetChatsListParser.parserGroupsJson ]')

        if json == None:
            return

        self.debug("[ GOT  ] groups: {}".format('chats' in json))

        is_manager = self.chatApi.isCurrentUserManager()

        if "chats" in json:

            chats_array = json["chats"]
            last_messages = json["messages"]

            live_managers_list = json.get("live_managers", [])
            live_managers = {}
            for _uid, _ch_id in live_managers_list:
                live_managers[_ch_id] = str(_uid)

            delivered_all = 0

            chats_d = {}

            for row in chats_array:
                if type(row) == dict:
                    row = (row['id'], row['name'], row['type'], None, None, 0, -1) # FIXME !!!

                chat_id = row[0]
                name = row[1]
                _type = row[2]
                delivered = row[5]
                cochat = row[6] if len(row) > 6 else -1
                if cochat == None:
                    cochat = -1
                marked_last = row[7] if len(row) > 7 else 0
                chat = None

                may_add_delivered = True
                if _type == "group":
                    chat = GroupChat(name, chat_id, cochat=cochat)
                    chat.badges_count = delivered
                    chats_d[chat_id] = chat
                    self.chatApi.chats.append(chat)

                elif _type == "private":
                    if row[4] == None:
                        usrs = [u for u in row[1].split('-')[1].split(',')]
                    else:
                        usrs = [str(row[4])]
                    for user_id in usrs:
                        if user_id in self.chatApi.users:
                            # if str(self.chatApi.user_id) == user_id: # FIXME !!!!!!!!!!!!!!!!!!!!!!!!!!!
                            #     continue
                            user = self.chatApi.users[user_id]
                            user.chat.chat_id = chat_id
                            user.chat.badges_count = delivered
                            chats_d[chat_id] = chat = user.chat

                elif _type == "live":
                    if not is_manager:
                        may_add_delivered = False

                    guest_login = row[3]
                    guest_id = row[4]

                    chat = LiveChat(name, chat_id, guest_login=guest_login, guest_id=guest_id, cochat=cochat)
                    chat.badges_count = delivered if may_add_delivered else 0

                    if chat_id in live_managers:
                        chat.live_manager = live_managers.get(chat_id)

                    chats_d[chat_id] = chat
                    self.chatApi.chats.append(chat)

                if chat:
                    chat.marked_last = marked_last

                if may_add_delivered:
                    if delivered > 0:
                        delivered_all += delivered

            for row in last_messages:
                if type(row) == dict:
                    row = (row['chat_id'], row['date'], row['sender'], row['message'], row['id'], row['ts']) # FIXME !!!

                chat_id = row[0]
                last_time = row[1]
                last_sender = row[2]
                last_message = row[3]
                if len(row) > 4:
                    last_id = row[4]
                else:
                    last_id = None

                chat = chats_d.get(chat_id)
                if chat:
                    chat.last_message = Message(last_message, mes_id=last_id)

                    if last_sender:
                        chat.last_message.sender_id = last_sender

                    if last_time:
                        chat.last_message.setTime(last_time)

            if delivered_all > 0:
                ChatApiCommon.doNotify("You have " + str(delivered_all) + " new messages")#, -1, "-1", 3)

            self.chatApi.setBadges(delivered_all)

            self.chatApi.doConnectStarted = None

            if self.chatApi.callbacks:
                self.chatApi.callbacks.gotChatsListCallback(self.chatApi.chats)

            self.chatApi.logger.info("clear last active state")

            self.chatApi.mouse_pos_change_control.clear_current_state()
