from threading import active_count
from json import dumps, loads
from time import sleep
import os, sys
from copy import copy
from datetime import datetime

from .BaseParser import BaseParser
from . import ChatApiCommon
from .ChatApiCommon import tryable, in_thread, by_timer, getGlobalMousePos, get_server_data_path, ALPHAVET_FULL
from ..datas.User import User
from ..datas.UserChat import UserChat
from ..datas.GroupChat import GroupChat
from ..file_load.FileLoadBase import FileLoadBase
from ..file_load.FileDownloadJob import FileDownloadJob
from ..file_load.Updater import Updater
from .api_object import ApiObject
from bp_chat.logic.common.log import get_logger
from bp_chat.core.local_db_messages import LocalDbMessagesMap
from bp_chat.gui.common import langs
from .ChatApiBases import *
from .ChatApiCallbacks import *
from bp_chat.core.tryable import ConsoleThread

# from pympler import muppy
# from pympler import summary


@ApiObject.init
class ChatApi(ChatApiConnect):

    __instance = None
    __start_args = None

    # ------- Logged in CRITICAL - -------

    _login = None
    _pwd = None
    _register = False

    resendMessage = None
    #resendMessageToOtherChat = False

    filesProgresses = {}
    last_chat_id = -1
    last_chat_id_for_scroll = -1
    _getting_last_messages = None

    # ------------------------------------

    parsers = None
    gui_visible = False
    scrollChatToBottom = True
    auto = None

    jobFileDownload = -1
    jobFileDownloadType = FileLoadBase.FILE_DOWNLOAD
    jobChatApi = -1
    jobChatApiStarted = None

    _delivered_sender = None
    _timer = None
    _timer_stop = False
    last_get_last_version = None
    last_check_profiles = None

    _updater = None
    update_local_path = None
    need_check_update = True
    may_send_active = True
    need_work = True

    __executor = None

    images = None
    http = "https"
    wss = "wss"

    opening_profile_id = None

    @staticmethod
    def instance(argv=None, **kwargs) -> 'ChatApi':
        if argv:
            ChatApi.__start_args = argv
        if not ChatApi.__instance:
            # if ChatApi.__start_args and 'imit' in ChatApi.__start_args:
            #     from .ImitChatApi import ImitChatApi
            #     cls = ImitChatApi
            # else:
            #     cls = ChatApi
            ChatApiCommon.getDeviceId(first_start=True)
            ChatApi.__instance = ChatApi(**kwargs)
        return ChatApi.__instance

    def __init__(self, **kwargs):
        self.init_connecting()
        self.init_state(kwargs)

        self.loadPrefs()
        self.start()

        self._updater = Updater(self)

    @tryable
    def parseInput(self, data):
        # print(" Got parseInput:")
        # print(data)
        json = loads(data)

        parser = self.get_answer_parser(json)
        if parser != None:
            pname = parser.__class__.__name__
            if pname != 'CommonDataParser':
                self.logger.info("got {}".format(pname))
            parser.execute(json)
        elif BaseParser.is_error(json):
            self.debug(" Got error answer (0): {}".format(json))

        elif BaseParser.is_answer(json, "get_chat_users") and BaseParser.is_success(json) and "result" in json:
            result = json["result"]
            users_checked = []
            self.debug(" get_chat_users: " + str(result))

            for user in result:
                user_id = user[0]
                users_checked.append(user_id)
                self.debug("get_chat_users - " + "user_id: " + str(user_id))

            self.onGotChatUsersCall(users_checked)

        elif json.get("error", None) in ConnectParser.ConnectParser.ERROR_TYPES:
            if not self.parsers["connect"].onError(json):
                self.debug(" got unknown (2): " + str(json))

        else:
            self.debug(" got unknown: " + str(json))

    def logout(self):
        self.send(url="/users/logout/", attrs={})

        sleep(0.5)

        self.disconnect()

    def stopConnecting(self):
        # // FIXME stop connecting
        pass

    def on_chat_selected(self, chat):
        # // FIXME create private group
        chat_id = chat.id
        if chat_id < 0:
            chat_api = ChatApi.instance()
            if chat != None and chat.is_private() and chat_api.creatingChat == None:
                # FIXME : hack...
                chat_api.creatingChat = chat
                userChat = chat
                he_id = userChat.user.id
                chat_api.send(url="/group/", attrs={
                    "method": "POST",
                    "group_name": "private-" + str(chat_api.getCurrentUserId()) + "," + str(he_id),
                    "group_type": "private",
                    "users": str(chat_api.getCurrentUserId()) + "," + str(he_id)
                })
        self.showChat(chat_id, chat.getName())

    def onLoginOccupied(self):
        self.disconnect(DISCONNECT_ONCE)
        self.onLoginOccupiedCall()

    def onApiClientOld(self):
        self.debug("onApiClientOld")
        self.disconnect()
        self.onApiClientOldCall()

    def onApiServerOld(self):
        self.debug("onApiServerOld")
        self.disconnect()
        self.onApiServerOldCall()

    def setLoginAndPwd(self, login, pwd):
        self._login = login
        self._pwd = pwd

    def getUsersAvatars(self):
        if self.users and len(self.users) > 0:
            users = ",".join(self.users.keys())
            self.send(url="/users/avatar/", attrs={"users": users })

    def getUserProfile(self, _user_id, live_chat_id=None, hidden=False):
        #return # FIXME AAAAAAAAAAAAAAAAAAAAAAA
        if live_chat_id == None:
            d = {"user_id": _user_id }
            if not hidden:
                self.opening_profile_id = _user_id
        else:
            d = {'live_chat_id': live_chat_id}
        self.send(url="/user/profile/", attrs=d)

    def createGroupChat(self, group_name, checked_users):
        self.creatingChat = GroupChat(group_name, -1)
        users_s = ",".join(checked_users)
        self.send(url="/group/", attrs={
            "method": "POST",
            "group_type": "group",
            "group_name": group_name,
            "users": users_s
        })

    def removeMeFromGroupChat(self, chat_id):
        self.send(url="/group/change/", attrs={
            "method": "POST",
            "chat_id": chat_id
        })

    def sendMessage(self, message_text):
        resendMessage = self.resendMessage
        if resendMessage != None:
            self.onSendMessageCall()

            resend_filesize = ""
            resend_message = resendMessage.text

            resend_file = resendMessage.getFile()
            resend_filename = resendMessage.getFileName()

            if resend_file in (None, '0', 0): # FIXME
                resend_file = ""
                resend_filename = ""
            else:
                resend_filesize = resendMessage.file_size
                resend_message = "" #// FIXME

            quote = ( "[QUOTE sender=" + resendMessage.getSender().name + "; sender_id=" +
                    str(resendMessage.getSender().id) + "; file=" + resend_file + "; file_name=" + resend_filename +
                    "; file_size=" + str(resend_filesize) + "]" + resend_message + "[/QUOTE]" )

            message_text = quote + message_text

        message_text = self.fix_text(message_text)

        self.send(url="/message/", attrs={"chat_id": self.getCurrentChatId(), "message": message_text})

    def deleteMessages(self, ids_list):
        chat_id = self.getCurrentChatId()
        user_id = self.getCurrentUserId()
        self.send(url="/message/delete/", attrs={"messages": ids_list, "chat_id": chat_id, "user_id": user_id})

    @staticmethod
    def fix_text(message_text):
        return ''.join([m for m in message_text if m in ALPHAVET_FULL])

    def sendMessageSmart(self, text):
        if len(text.strip()) == 0 and not self.resendMessage:
            return

        lines = text.split('\n')
        new_lines = []
        quote, q_last = [], -1
        for i, line in enumerate(lines):
            lstr = line.lstrip()
            if lstr.startswith('>>') and (q_last < 0 or q_last == i-1):
                q_last = i
                quote.append(lstr[2:])
            else:
                new_lines.append(line)

        text = '\n'.join(new_lines)
        if len(quote) > 0:
            text = '[QUOTE]{}[/QUOTE]'.format('\n'.join(quote)) + text

        self.sendMessage(text)

    def sendApi(self, **kwargs):
        self.send(url="/api/", attrs=kwargs)

    def sendFile(self, data=None, image=None, filepath=None, user_avatar=None, show_sending_file=False):
        if show_sending_file:
            self.showError("Sending file...") # FIXME

        if image:
            filename = ChatApiCommon.createImageFileName()
            dirpath = os.path.dirname(filename)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            image.save(filename)
            data = {
                'uri': filename, "fileName": os.path.basename(filename), 'fileSize': os.path.getsize(filename)
            }
        elif filepath:
            filepath = os.path.normpath(filepath)
            data = {
                'uri': filepath, "fileName": os.path.basename(filepath), 'fileSize': os.path.getsize(filepath)
            }

        if data == None:
            FileDownloadJob.runJobUploadByCreatedFile(self.current_chat_id, self.createdFile.size(), os.path.basename(self.createdFile.name))
        else:
            uri = data.get('uri')
            fileName = data.get('fileName')
            fileSize = data.get('fileSize')
            FileDownloadJob.runJobUploadByUri(uri, fileName, fileSize, self.current_chat_id, user_avatar)

    def downloadFile(self, fileId, fileName):
        FileDownloadJob.runJobDownload(fileId, fileName)

    def mark_last_read(self, chat_id, message_id):
        self.send(url='/message/mark_last_read/', attrs={
            "method": "POST",
            'chat_id': int(chat_id),
            'message_id': int(message_id),
        })

    def unmark_last_read(self, chat_id):
        self.send(url='/message/mark_last_read/', attrs={
            "method": "POST",
            'chat_id': int(chat_id),
            'unmark': True,
        })

    def take_live_chat(self, chat_id):
        self.send(url='/group/live/take/', attrs={
            'user': int(self.getCurrentUserId()),
            'chat_id': chat_id
        })

    def finished_live_chat(self, chat_id):
        self.send(url='/group/live/take/', attrs={
            'method': 'POST',
            'user': int(self.getCurrentUserId()),
            'chat_id': chat_id
        })

    def create_cochat(self, chat_id):
        self.send(url='/group/live/cochat/', attrs={
            'method': 'POST',
            'chat_id': chat_id
        })

    def makeAdmin(self, user_id):
        self.send(url='/users/role/', attrs={
            'method': 'POST',
            'com': 'make_admin',
            'user_id': user_id
        })

    def activateUser(self, user_id, active):
        self.send(url='/admin/user/activate/', attrs={
            'method': 'POST',
            'user_id': user_id,
            'active': active
        })

    def open_cochat(self, chat_id):
        pass

    def get_server_settings(self):
        self.send(url='/server/settings/', attrs={})

    def set_server_settings(self, sets):
        d = {'method':'POST'}
        d.update(sets)
        self.send(url='/server/settings/', attrs=d)

    def getCurrentUserId(self):
        return self.user_id

    def getCurrentUser(self):
        return self.getUser(self.getCurrentUserId())

    def isCurrentUserManager(self):
        return self.getCurrentUser().is_manager()

    def createUser(self, nick, id, status, user_type, is_bot=False):
        user = User(nick, id, user_type, is_bot)
        if "online" == status:
            user.status = User.STATUS_ONLINE
        elif "sleep" == status:
            user.status = User.STATUS_SLEEP
        else:
            user.status = User.STATUS_OFFLINE
        self.createUserChat(user, id)
        self.load_user_profile()

    @in_thread
    def load_user_profile(self, user):
        user.load()

    def createUserChat(self, user, id):
        chat = UserChat(user)
        user.chat = chat
        self.users[id] = user
        self.chats.append(chat)

    def updateStatuses(self, online, offline, sleep):

        changed = self.updateStatusesFromJsonArray(online, User.STATUS_ONLINE)
        changed |= self.updateStatusesFromJsonArray(offline, User.STATUS_OFFLINE)
        changed |= self.updateStatusesFromJsonArray(sleep, User.STATUS_SLEEP)

        if changed:
            self.onChatsUpdatedListCall()

    def updateStatusesFromJsonArray(self, jsonArray, toStatus):
        changed = False
        for val in jsonArray:
            try:
                offline_user_id = str(val)
                offline_user = self.getUser(offline_user_id)
                if offline_user != None:
                    offline_user.status = toStatus
                    changed = True
            except Exception as e:
                self.debug("JSONException (updateStatusesFromJsonArray): " + str(e)) # FIXME

        return changed

    def openChat(self, chat_id):
        self.opening_chat_id = chat_id
        self.closeCurrentChat()

        max_id = self.getMessagesFromLocalDb(chat_id, with_update_gui=False)
        if max_id:
            self.setChatOpened()
            self.updateChatMessagesGui()

        url, attrs = self.makeMessageRangeSend(chat_id, after_id=max_id)
        return self.send(url=url, attrs=attrs, debug_full=True)

    def getMessagesFromLocalDb(self, chat_id, last_message=0, range=20, with_update_gui=True, only=None):
        #return
        count = 0
        min_prev_id = self.getMinMessagesPrevId()
        start = datetime.now()
        max_id = 0
        found_prev = False if min_prev_id != None else True
        found_bad_prev = False

        meses = list(LocalDbMessagesMap.get_range(self.server_uid, chat_id, last_message=last_message, range=range, only=only))

        end = datetime.now()
        dt = end - start

        for m in meses:
            self.insertMessage_to_currentChat_withoutDb(m.mes_id, m)
            if m.mes_id != None and m.mes_id > max_id:
                max_id = m.mes_id
            if not found_prev and m.mes_id == min_prev_id:
                found_prev = True
            count += 1

        last_m_id = None
        for m in sorted(meses, key=lambda m: m.mes_id):
            if last_m_id != None:
                if m.prev_id != last_m_id:
                    found_bad_prev = True
                    break
            last_m_id = m.mes_id

        end = datetime.now()
        dt = end - start

        if count > 0 and with_update_gui:
            self.updateChatMessagesGui()

        return max_id if found_prev and not found_bad_prev else 0

    def closeCurrentChat(self):
        self.clearGettingLastMessages()
        self.current_chat_id = -1
        self.clearCurrentChat()

    def clearGettingLastMessages(self):
        self._getting_last_messages = None

    def getLastMessagesOnCurrentChat(self, last_message, range=20):
        chat_id = self.current_chat_id
        if self.getMessagesFromLocalDb(chat_id, last_message=last_message):
            return
        url, self._getting_last_messages = self.makeMessageRangeSend(chat_id, last_message=last_message, range=range)
        self.send(url=url, attrs=self._getting_last_messages, debug_full=True)

    def makeMessageRangeSend(self, chat_id, last_message=0, range=20, after_id=0):
        attrs = {"range": range, "last_message": last_message, "chat_id": chat_id, "after_id": after_id}
        return "/message/range/", attrs

    def clearCurrentChat(self):
        self.current_chat_messages = CurrentChatMessages()
        self.updateChatMessagesGui()

    def insertMessage_to_currentChat(self, key, message):
        message.got_time = 1                                            # FIXME
        LocalDbMessagesMap.insert_message_got(message, self.server_uid)
        self.insertMessage_to_currentChat_withoutDb(key, message)

    def insertMessage_to_currentChat_withoutDb(self, key, message):
        self.current_chat_messages.insert(int(key), message)

    def getMinMessagesPrevId(self):
        prevs = [m.prev_id for m in self.current_chat_messages.get_messages() if m.prev_id != None]
        prevs = sorted(prevs)
        if len(prevs) == 0:
            return None
        last_prev = prevs[-1]
        for p in prevs[::-1]:
            if p - last_prev > 1:
                break
            last_prev = p
        return last_prev

    def getUser(self, id):
        return self.users.get(str(id))

    def getUserOrCreate(self, id, nick, user_type, is_bot):
        user = self.getUser(id)
        if not user:
            self.createUser(nick=nick, id=id, user_type=user_type, is_bot=is_bot, status=None)
        return self.getUser(id)

    def getChatName(self, chat_id, full=True):
        chat = self.getChatById(chat_id)
        if chat != None:
            return chat.getName(full=full)
        return None

    def getChatById(self, chat_id):
        if chat_id >= 0:
            for chat in self.chats:
                if chat.chat_id == chat_id:
                    return chat
        return None

    def getChatsByName(self, chat_name):
        chats = []
        for chat in self.chats:
            if chat.getName() == chat_name:
                chats.append(chat)
        return chats

    def setGuiVisible(self, value):
        self.gui_visible = value

    def isGuiVisible(self):
        return self.gui_visible

    def addBadgesToChat(self, chat_id, badges, cause=""):
        chat = self.getChatById(chat_id)
        if chat != None:
            sign = "" if badges < 0 else "+"
            chat.badges_count += badges
            if chat.badges_count < 0:
                chat.badges_count = 0
            self.addBadges(badges)

    def getChatsWithBadgesCount(self):
        count = 0
        for chat in self.chats:
            if chat.badges_count > 0:
                count += 1
        return count

    def isUserGuest(self):
        return self.user_type != None and self.user_type == User.USER_TYPE_GUEST

    def setResendMessage(self, message, other_chat=False):
        self.resendMessage = message
        # if other_chat:
        #     self.resendMessageToOtherChat = other_chat
        # else:
        #     self.resendMessageToOtherChat = ChatApi.instance().getCurrentChatId()

    def setCurrentUserProfile(self, up):
        self.userProfile = up

    def getCurrentUserProfile(self):
        return self.userProfile

    def getCurrentUserLogin(self):
        return self.getCurrentUserProfile().getUserLogin()

    def setCurrentChatId(self, chat_id):
        self.current_chat_id = chat_id

    def getCurrentChatId(self):
        return self.current_chat_id

    def getCurrentChat(self):
        return self.getChatById(self.getCurrentChatId())

    def getCurrentOrOpeningChatId(self):
        if self.current_chat_id > 0:
            return self.current_chat_id
        return self.opening_chat_id

    def setOpeningChatId(self, chat_id):
        self.opening_chat_id = chat_id

    def getOpeningChatId(self):
        return self.opening_chat_id

    def setChatOpened(self):
        chatOpened = self.getOpeningChatId()
        self.setCurrentChatId(chatOpened)
        self.setOpeningChatId(-1)
        self.setLastChatOpenedTime(datetime.now())
        if self.callbacks != None:
            self.callbacks.chatOpenedCallback(chatOpened, False)
        return chatOpened

    def setLastChatOpenedTime(self, t):
        self.last_chat_opened_time = t

    def saveLastMessageForChatsWhenOpens(self, message):
        self.lastMessages.append(message)

    def fillChatsFromSavedLastMessages(self):
        chats_changed = False
        for message in self.lastMessages:
            chats_changed |= self.updateChatLastText(self.getCurrentUserId(), message)
        self.lastMessages = []
        return chats_changed

    def updateChatLastText(self, current_user_id, message):
        if message.chat_id >= 0:
            # Chat chat = None
            for ch in self.chats:
                if ch.chat_id == message.chat_id:
                    if ch.last_message == None or ch.last_message.getTimestamp() <= message.getTimestamp():
                        ch.last_message = message
                        if not message.getDelivered() or message.sender_id != current_user_id:
                            # FIXME
                            pass
                        return True
        return False

    def getChatEditUsers(self, chat_id):
        self.send(url="/group/users/", attrs={"chat_id": chat_id})

    def updateAvatar(self, file, data, source=None):
        _add = '' if source == None else ' source: {}'.format(source)
        self.users_avatars[file] = data

        count = 0
        for user in self.users.values():
            if user.profile.getPhotoId() == file:
                count += 1
                if self.userProfile != None and user.id == self.userProfile.getUserID():
                    self.currentUserProfileUpdated()

        if count > 0:
            self.onGotAvatarCall()

    def currentUserProfileUpdated(self):
        is_mine = str(self.userProfile.getUserID()) == str(self.getCurrentUserId())
        if is_mine:
            self.onCurrentUserProfileUpdatedCall()

    def getPhotoData(self, photo_id):
        return self.users_avatars.get(photo_id)

    def setCreatedFile(self, val):
        self.createdFile = val

    def setJobFileDownload(self, jobId):
        self.jobFileDownload = jobId

    def setJobFileDownloadType(self, type):
        self.jobFileDownloadType = type

    def getDeliveredSender(self, cls):
        if not self._delivered_sender and cls != None:
            self._delivered_sender = cls()
        return self._delivered_sender

    def getAppName(self):
        name = "BP Chat"
        if self.is_admin:
            name += " (admin)" # FIXME someone merged it wrong...
        return name

    @tryable
    def _on_message(self, ws, data):
        self.parseInput(data)

    @tryable
    def send(self, url, attrs, debug=True, debug_full=False):
        if not self._connected_ws:
            return
        if debug:
            _u = url
            if debug_full:
                _u += " attrs: {}".format(attrs)
        self.logger.info("send {}".format(_u))
        d = {
            'url': url,
            'attrs': attrs
        }
        self._connected_ws.send(dumps(d))

    def sendActive(self, active, initial=False):
        if self.may_send_active or initial:
            self.send(url='/user/active/', attrs={'active':active})

    def get_answer_parser(self, json):
        try:
            if "answer" in json:
                answer = json.get("answer")
                return self.parsers.get(answer)
        except Exception as e:
            self.debug(" JSON Exception: " + str(e))
        return None

    #@by_timer(0.1)
    @tryable
    def startDownloadUpdate(self, **kwargs):
        #self._updater.start_download(**kwargs)
        ret, txt = Updater.start_updater()
        if ret and txt:
            self.callbacks.needShowSmartInfo(txt)

    def startUpdate(self):
        self._updater.start_update()

    @classmethod
    def start_update_clicked(cls):
        d = ChatApi.instance().need_check_update
        if type(d) == dict and d['on_stop']:
            d['on_stop']()
        if d == True:
            d = {'need_check_update': True}
        elif not d:
            d = {}
        ChatApi.instance().startDownloadUpdate(**d)
        ChatApi.instance().close_app_now()

    def check_update_local(self):
        self._updater.check_update_local()

    def start(self):
        if not self._timer and self.with_thread:
            self._timer = True
            self.check_updates_thread()

    @in_thread
    def check_updates_thread(self):
        while not self._timer_stop:
            if hasattr(self, "MAY_CLOSE_NOW"):
                return

            self._work()

            sleep(15)

    def _work(self):
        self._work_reconnect()
        self._work_update()
        self._work_GlobalMousePos()

    @tryable
    def _work_reconnect(self):
        if self.started:
            if not self.is_connected() and not self.is_connecting_good():
                self.do_connect()

    @tryable
    def _work_update(self):
        if self.need_check_update:
            if not self.last_get_last_version or (datetime.now()-self.last_get_last_version).total_seconds() > 3600: # every hour
                self.last_get_last_version = datetime.now()
                self.getLastVersion(self.need_check_update)

            if not self.last_check_profiles:
                self.last_check_profiles = datetime.now()
                self.checkProfiles()
            elif (datetime.now()-self.last_check_profiles).total_seconds() > 5: #300: # 5 minutes
                self.last_check_profiles = datetime.now()
                self.checkProfiles()

            #self.check_memory()

    sum_last = None

    def check_memory(self):
        pass
        # all_objects = muppy.get_objects()
        # mem_len = len(all_objects)
        # my_types = muppy.filter(all_objects, Type=type)
        # types_count = len(my_types)
        
        # sum1 = summary.summarize(all_objects)

        # print(f'mem_len: {mem_len} types_count {types_count}')
        # self.logger.info(f'mem_len: {mem_len} types_count {types_count}')

        # if self.sum_last != None:
        #     diff = summary.get_diff(self.sum_last, sum1)
        #     print('ALL OBJECTS - DIFF:')
        #     summary.print_(diff)
        # else:
        #     print('ALL OBJECTS:')
        #     summary.print_(sum1)

        # self.sum_last = sum1

    TIMOUT_TO_RESEND_ACTIVE = 5 * 60
    last_active_sended_dt = None

    @tryable
    def _work_GlobalMousePos(self):
        now = datetime.now()
        if not self.last_active_sended_dt or (now - self.last_active_sended_dt).total_seconds() >= self.TIMOUT_TO_RESEND_ACTIVE:
            self.mouse_pos_change_control.set_sended(False)

        pos = getGlobalMousePos()

        state = self.mouse_pos_change_control.check_new_value_changed(pos)
        if state != None or not self.mouse_pos_change_control.is_sended():
            if state == None:
                state = self.mouse_pos_change_control.get_current_state()
            if state != None:
                self.logger.info('sNEW STATE: active={}'.format(state))
                self.sendActive(state)
                self.mouse_pos_change_control.set_sended()
                self.last_active_sended_dt = now

    check_profiles_works = False

    def checkProfilesFin(self):       
        print('[ checkProfilesFin ] --> OK')
        self.check_profiles_works = False

    @by_timer(3, on_finish=checkProfilesFin)
    @tryable
    def checkProfiles(self):
        print('[ checkProfiles ]', datetime.now())
        if self.check_profiles_works:
            return
        self.check_profiles_works = True
        count_need_to_load = 0
        count_loaded = 0
        first_to_get = None
        for chat in self.chats:
            if chat.is_private():
                name = chat.getLogin()
                name2 = chat.getNameByProfile()
                if not name2 or name2 == name:
                    ret = chat.user.profile.load(initial=False)
                    if ret:
                        print('>>>', name, '---', name2)
                        count_loaded += 1
                    else:
                        if ret == None:
                            return
                        print('>>> NEED LOAD:', name, '---', name2)
                        count_need_to_load += 1
                        if first_to_get == None:
                            first_to_get = chat

        if first_to_get:
            print('[ checkProfiles ] first_to_get:', first_to_get.user.id)
            self.getUserProfile(first_to_get.user.id, hidden=True)

        if count_loaded > 0:
            print('[ checkProfiles ] count_loaded:', count_loaded)
            self.callbacks.chatsUpdatedListCallback()

    @by_timer(1)
    @tryable
    def getLastVersion(self, d=None):
        # if type(d) != dict:
        #     d = {'app': 'bp_chat', 'url':'chat-win-client'}
        self.logger.info("start getLastVersion")
        if self.update_local_path:
            _updat_path =  os.path.join(os.path.abspath(self.update_local_path), 'bp_chat.update')
            if os.path.exists(_updat_path):
                data = open(_updat_path, 'rb').read()
                s = ''
                i = len(data) - 1
                while i >= 0:
                    a = data[i:i + 1].decode('utf-8')
                    if a == '|':
                        break
                    s = a + s
                    i -= 1
                last_version = s
            else:
                last_version = "-"
        else:
            last_version = Updater.load_last_version(d)
            if not last_version:
                return

        try:
            last_greater = self.check_last_version(last_version)
        except:
            return

        if last_greater or "TST_UPDATE" in sys.argv:
            self.onLastVersionGreater(last_version)
        else:
            pass
        #self.check_update_local()

    def check_last_version(self, last_version):
        good = "m" not in last_version and "n" not in last_version
        if not good:
            return

        last_greater = False
        app_version = self.app_version
        if app_version and ("m" in app_version or "n" in app_version):
            last_greater = True

        if not last_greater:
            lsv = [ int(a) for a in last_version.split('.') ]
            asv = [ int(a) for a in app_version.split('.') ] if self.app_version else [1, 1, 1]
            last_greater = lsv > asv

        return last_greater

    @property
    def logger(self):
        if not self.with_logger:
            class _Logger:
                def info(self, *args,**kwargs):pass
                def warning(self, *args,**kwargs):pass
            return _Logger()
        return get_logger()

    @tryable
    def finish(self):
        for w in self.ws_apps:
            w.close()

        if self._timer:
            self._timer_stop = True
        deliveredSender = self.getDeliveredSender(None)
        if deliveredSender:
            deliveredSender.shutdown()




if __name__=='__main__':

    api = ChatApi()
    api.connect()

    import time
    time.sleep(10)
