
from datetime import datetime

from .api_object import ApiObject
from .BaseParser import BaseParser
from ..datas.GroupChat import GroupChat
from ..datas.LiveChat import LiveChat
from ..datas.UserChat import UserChat
from .ChatApiCommon import tryable
from .DeliveredSender import DeliveredSender


class UpdateParser(ApiObject):

    _last_amfimo_dt = None

    @tryable
    def onSuccess(self, result):
        update = result["update"]

        if self.is_status(update):
            self.chat_api.logger.info("got statuses")

            online = None
            offline = None
            sleep = None
            if "online" in update:
                online = update["online"]
            if "offline" in update:
                offline = update["offline"]
            if "sleep" in update:
                sleep = update["sleep"] # FIXME in android
            self.chat_api.updateStatuses(online, offline, sleep)

            return True

        elif BaseParser.is_user_new(update):
            self.chat_api.logger.info("got user_new")

            if "id" in update and "name" in update:
                user_new_id = str(update["id"])
                user_new_name = update["name"]
                user_new_type = update.get("user_type", 0)
                user_is_bot = update.get("is_bot", False)
                self.chat_api.createUser(nick=user_new_name, id=user_new_id, user_type=user_new_type, is_bot=user_is_bot,
                                        status=None)

                self.updateChats()

        elif BaseParser.is_user_change(update):
            self.chat_api.logger.info("got user_change")

            if "id" in update and ("name" in update or "changed_type" in update):
                user_change_id = update["id"]
                user_change_name = update.get("name", None)
                user_changed_type = update.get("changed_type", None)

                if user_changed_type != None:
                    if str(user_change_id) == str(self.chat_api.getCurrentUserId()):

                        # FIXME need go to login
                        self.chat_api.disconnectForReconnect()
                        return True
                    else:
                        user = self.chat_api.users.get(user_change_id)
                        if user:
                            user.setUserType(user_changed_type)

                user = self.chat_api.users.get(user_change_id)
                if user_change_name and user:
                    user.name = user_change_name

                self.updateChats()

        elif BaseParser.is_user_del(update):
            self.chat_api.logger.info("got user_del")

            if "id" in update:
                user_del_id = update["id"]
                userObject = self.chat_api.users.get(user_del_id)
                if userObject != None:
                    user = userObject
                    # FIXME
                    self.chat_api.chats.remove(user.chat)
                    del self.chat_api.users[user_del_id]

                    self.updateChats()

        elif BaseParser.is_group(update) or BaseParser.is_live(update) or BaseParser.is_user_to_group(update) or BaseParser.is_private(update):
            self.chat_api.logger.info("got group")

            if "room_name" in update:

                chat_id = -1
                if "room_id" in update:
                    chat_id = update.get("room_id")
                elif "chat_id" in update: # FIXME simple hack
                    chat_id = update.get("chat_id")

                chat_id = int(chat_id) # FIXME it is a sever problem, we know about it, so why was not debugged ??? =)

                if chat_id >= 0:
                    chat_name = update["room_name"]

                    creatingChat = None
                    creater_user = None
                    if "user_id" in update:
                        creater_user = str(update.get("user_id"))

                        self.debug("...creating chat: user=" + creater_user + "({})".format(type(creater_user)) + "/" + str(self.chat_api.getCurrentUserId()) + " --> " + str(self.chat_api.creatingChat != None))

                        if creater_user == str(self.chat_api.getCurrentUserId()):
                            creatingChat = self.chat_api.creatingChat

                    if BaseParser.is_private(update):
                        creatingPrivateChat = creatingChat
                        if creatingPrivateChat != None: # FIXME check with who
                            self.chat_api.creatingChat = None
                            self.debug("<<< private chat created >>>")
                            creatingPrivateChat.chat_id = chat_id
                            self.chat_api.showError(None)
                            self.chat_api.setCurrentChatId(chat_id)
                        else:
                            self.debug("<<< someone created private chat >>>: {} ({})".format(chat_id, creater_user))
                            if creater_user:
                                user = self.chat_api.getUser(creater_user)
                                if user:
                                    creatingPrivateChat = UserChat(user)
                                    creatingPrivateChat.chat_id = chat_id
                                    user.chat = creatingPrivateChat
                                    self.chat_api.chats.append(creatingPrivateChat)


                    else:
                        creatingGroupChat = creatingChat
                        if creatingGroupChat != None:
                            if "user_id" in update: # FIXME check that chat is that
                                user_id = update.get("user_id")
                                if self.chat_api.getCurrentUserId() == user_id:
                                    creatingGroupChat.chat_id = chat_id
                                    self.chat_api.creatingChat = None
                                    self.debug("<<< group chat created >>>")  # FIXME maybe on opening mechanism??..
                                    self.chat_api.setCurrentChatId(chat_id)
                                    if self.chat_api.callbacks != None:
                                        self.chat_api.callbacks.chatOpenedCallback(chat_id, True)
                        else:
                            cochat = update.get('cochat', -1)
                            if cochat == None:
                                cochat = -1

                            if BaseParser.is_live(update):
                                creatingGroupChat = LiveChat(chat_name, chat_id, guest_id=creater_user, cochat=cochat)
                            else:
                                creatingGroupChat = GroupChat(chat_name, chat_id, cochat=cochat)

                            if cochat >= 0:
                                cochat_chat = self.chat_api.getChatById(cochat)
                                if cochat_chat:
                                    cochat_chat.set_cochat(chat_id)

                        self.chat_api.chats.append(creatingGroupChat)

                    self.updateChats()


        elif BaseParser.is_chat_change(update):
            self.chat_api.logger.info("got chat_change")

            if "room_id" in update and "room_name" in update:
                chat_id = update.get("room_id")
                chat_name = update.get("room_name")

                chat = self.chat_api.getChatById(int(chat_id))
                if chat != None:
                    if not chat.is_private():
                        group = chat
                        group.set_name(chat_name)
                        cochat = update.get('cochat', -1)
                        if cochat >= 0 and group.cochat != cochat:
                            group.set_cochat(cochat)

                self.updateChats()

        elif BaseParser.is_chat_del(update) or BaseParser.is_user_from_group(update):
            self.chat_api.logger.info("got chat_del")

            chat_id = -1

            if "room_id" in update:
                chat_id = int(update.get("room_id"))
            elif "chat_id" in update: # FIXME simple hack...
                chat_id = int(update.get("chat_id"))

            if chat_id >= 0:

                chat = self.chat_api.getChatById(chat_id)
                if chat != None:
                    if chat.is_private():
                        chat.chat_id = -1
                        chat.last_message = None
                    else:
                        self.chat_api.chats.remove(chat)

                self.updateChats()

        elif BaseParser.is_chat_activate(update):
            self.chat_api.logger.info("got chat_activate")

            if "id" in update.has("id"):
                chat_id = int(update.get("id"))
                if "chat_name" in update and "chat_type" in update:
                    chat_name = update.get("chat_name")
                    chat_type = update.get("chat_type")

                    chat = self.chat_api.getChatById(chat_id)
                    if chat == None:

                        if "group" == chat_type:
                            group = GroupChat(chat_name, chat_id)
                            self.chat_api.chats.add(group)
                        else:
                            update.has("users")
                            # createUserChat()

                        self.updateChats()

        elif BaseParser.is_delivered(update):
            self.chat_api.logger.info("got delivered")

            if "delivered" in update:
                delivered = update["delivered"]
                DeliveredSender.getInstance().difference(delivered)

            elif "messages" in update:
                # FIXME .... ???
                pass

        elif BaseParser.is_not_delivered(update):
            update = update["not_delivered"]

            chat_id = int(update.get("chat_id"))
            not_delivered = int(update.get("not_delivered"))
            marked_last = int(update.get("marked_last"))

            chat = self.chat_api.getChatById(chat_id)
            if chat != None:
                chat.badges_count = not_delivered
                chat.marked_last = marked_last
                self.updateChats()

        elif BaseParser.is_take_live_chat(update):
            self.chat_api.logger.info("got take_live_chat")

            live_status = update.get("status")
            chat_id = int(update.get("chat_id"))
            live_manager = -1
            if live_status == 'started':
                live_manager = update.get('user_id')

            chat = self.chat_api.getChatById(chat_id)
            if chat != None:
                chat.live_manager = str(live_manager) # FIXME

                self.updateChats()

        elif BaseParser.is_adm_info(update):
            if not self._last_amfimo_dt or (datetime.now() - self._last_amfimo_dt).total_seconds() < 3:
                self.chat_api.logger.info("got amfimo")

            self._last_amfimo_dt = datetime.now()

            if self.chat_api.is_admin:
                adm_info = update.get("adm_info")
                if adm_info:
                    if self.chat_api.callbacks:
                        self.chat_api.callbacks.onAdmInfo(adm_info)

        elif BaseParser.is_open_chat(update):
            open_chat = update.get("open_chat")
            if open_chat:
                self.chat_api.raiseWindow()
                open_chat_id = open_chat.get('chat_id')

                self.chat_api.showChat(open_chat_id, None)

        else:
            return False

        return True

    def updateChats(self):
        if self.chat_api.callbacks != None:
            self.chat_api.callbacks.chatsUpdatedListCallback()

    def is_status(self, json):
        return BaseParser.is_type(json, "status")

    def debug(self, text):
        pass


