from datetime import datetime
from copy import copy
from time import sleep
import ssl, requests
from json import loads as json_loads
from contextlib import contextmanager
from websocket import WebSocketApp
import urllib3

from bp_chat.logic.common.app_config import AppConfig, ConnectConfig
from bp_chat.gui.common import langs
from bp_chat.logic.chat_api.connect import GetUsersListParser, ConnectParser, GetUsersAvatarParser, GetChatsListParser
from . import GetProfileParser, CommonDataParser, GetServerSettingsParser, GetServerInfoParser
from .ChatApiCommon import (tryable, in_thread, by_timer, getDeviceId, md5Apache, isUrlHttp, ChangeControl, get_server_data_path)
from .CurrentChatMessages import CurrentChatMessages
from ..FileLoader import FileLoader
from ...core.local_db_messages import LocalDbMessagesMap

DISCONNECT_FULL = 'FULL'
DISCONNECT_ONCE = 'ONCE'
DISCONNECT_FOR_RECONNECT = 'RECONNECT'


class ChatApiConsts:

    #APP_NAME = APP_NAME
    #APP_TITLE = APP_TITLE
    CLIENT_API_VERSION = '1.4.100'

    ERROR_SIMPLE = "SIMPLE-ERROR"
    ERROR_NOSERVERS = "NO-SERVERS"
    ERROR_WRONG_SERVER_1 = "WRONG-SERVER-1"
    ERROR_WRONG_SERVER_2 = "WRONG-SERVER-2"
    ERROR_NO_CONNECT = "NO-CONNECT"
    ERROR_NO_AUTH_DEACTIVATED = "NO-AUTH-DEACTIVATED"
    ERROR_API_SERVER_OLD = "API_SERVER_OLD"
    ERROR_API_CLIENT_OLD = "API_OLD"
    ERROR_LOGIN_OCCUPIED = "LOGIN_OCCUPIED"

    APP_PREFERENCES = "bpchatsettings"
    SERVER_ADDRESS = "server_address"
    SERVER_ADDRESS_2 = "server_address_2"
    USER_NAME = "user_name"
    STARTED = "started"
    USE_SERVER_2 = "use_server_2"
    DOWNLOAD_FILE = "download_file"
    DOWNLOAD_FILE_TYPE = "download_file_type"


class ChatApiDebug:

    app_version = None

    def debug(self, text):
        print(text)

    def set_app_version(self, app_version):
        self.app_version = app_version


class ChatApiConf:
    serverAddress = None
    serverAddress2 = None
    useServer2 = False
    started = False
    user_name_start = None
    may_save_load_prefs = True

    _config = None

    def savePrefs(self):
        if not self.may_save_load_prefs:
            return

        self._config.server_server = self.serverAddress
        self._config.server_server2 = self.serverAddress2
        self._config.server_useServer2 = self.useServer2
        self._config.server_started = self.started
        self._config.server_user_name_start = self.user_name_start
        self._config.save()

    def loadPrefs(self):
        if not self.may_save_load_prefs:
            return

        conf = self.conf
        conf.load()

        self.serverAddress = conf.server_server
        self.serverAddress2 = conf.server_server2
        self.useServer2 = conf.server_useServer2
        self.started = conf.server_started
        self.user_name_start = conf.server_user_name_start

        if conf.user_lang != langs.CURRENT_LANG:
            langs.change_lang()

    def setPrefs(self, serverAddress, serverAddress2, useServer2, started, user_name_start):
        self.serverAddress = serverAddress
        self.serverAddress2 = serverAddress2
        self.useServer2 = useServer2
        self.started = started
        self.user_name_start = user_name_start

    @property
    def conf(self):
        if not self._config:
            self._config = AppConfig()
            langs.add_callback(self.on_changed_lang)
        return self._config

    def on_changed_lang(self):
        self._config.user_lang = langs.CURRENT_LANG
        self._config.save()

    def get_conf(self, title, name):
        conf = self.conf
        return self._config.get_value(title, name) if conf else None

    def set_conf(self, title, name, value):
        if not self.conf:
            return
        self._config.set_value(title, name, value)


class ChatApiState:
    is_admin = False
    user_type = None # FIXME
    user_id = None
    user_token = None
    server_uid = None

    badgeCount = 0
    _smart_info = None
    _smart_info_id = 0
    current_chat_messages: CurrentChatMessages = None
    users = None
    chats: list = None
    users_avatars = None
    lastMessages = None # FIXME ???
    messages = None  # FIXME
    current_chat = None

    current_chat_id = -1
    opening_chat_id = -1
    last_chat_opened_time = None
    userProfile = None
    currentServer = -1

    creatingChat = None
    createdFile = None

    server_connect_config: ConnectConfig = None

    def init_state(self, kwargs):
        self.images = {}
        self.chats = []
        self.users = {}
        self.messages = {}

        self.init_smart_info()

        self.ws_apps = []

        self.mouse_pos_change_control = ChangeControl(60)

        self.need_work = kwargs.get('need_work', True)
        self.may_save_load_prefs = kwargs.get('may_save_load_prefs', self.need_work)
        self.may_send_active = kwargs.get('may_send_active', self.need_work)
        self.need_check_update = kwargs.get('need_check_update', self.need_work)
        self.update_local_path = kwargs.get('update_local_path', None)
        self.with_thread = kwargs.get('with_thread', self.need_work)
        self.with_avatars = kwargs.get('with_avatars', self.need_work)
        self.with_groups = kwargs.get('with_groups', self.need_work)
        self.with_users = kwargs.get('with_users', self.need_work)
        self.with_avatars = kwargs.get('with_avatars', self.need_work)
        self.auth_hidden = kwargs.get('auth_hidden', False)

        self.need_my_messages = kwargs.get('need_my_messages', False)

        self.with_logger = kwargs.get('with_logger', True)

    def init_connect(self, server_uid):
        self.server_connect_config = ConnectConfig(server_uid)
        self.server_connect_config.load()

    def save_connect(self):
        self.server_connect_config.save()

    def setUserAndToken(self, token, user_id):
        self.user_token = token
        self.user_id = user_id
        self.server_connect_config.set_utkn(token)

    def load_user_token(self):
        token = self.server_connect_config.get_utkn()
        self.user_token = token

    def setServerUid(self, server_uid):
        self.server_uid = server_uid

    def is_chat_muted(self, chat_id):
        if self.server_connect_config:
            return True if self.server_connect_config.get_muted_chat(chat_id) else False
        return False

    def is_chat_pinned(self, chat_id):
        if self.server_connect_config:
            return True if self.server_connect_config.get_pinned_chat(chat_id) else False
        return False

    def is_message_in_favorites(self, mes_id):
        if self.server_uid:
            return LocalDbMessagesMap.get_message_favorite(self.server_uid, mes_id)
        return False

    def init_smart_info(self):
        self._smart_info = {}
        self._smart_info_id = 0

    def addBadges(self, badges):
        self.setBadges(self.badgeCount + badges)

    def setBadges(self, badges):
        if badges < 0:
            badges = 0
        self.badgeCount = badges
        self.applyBadges()

    def applyBadges(self):
        pass

    # FIXME new for android:
    def addSmartInfo(self, text):
        sm_id = self._smart_info_id + 1
        self._smart_info_id = sm_id
        self._smart_info[sm_id] = text
        self._showLastSmartInfo()
        return sm_id

    def showSmartInfo(self, sm_id, text):
        self._smart_info[sm_id] = text
        self._showLastSmartInfo()

    def delSmartInfo(self, sm_id):
        if sm_id in self._smart_info:
            del self._smart_info[sm_id]
        self._showLastSmartInfo()

    def _showLastSmartInfo(self):
        pass


class ChatApiCallbacksPoint(ChatApiState):

    callbacks = None

    def connect_callbacks(self, callbacks):
        self.callbacks = callbacks

    def on_need_show_find_in_chat(self):
        if self.callbacks:
            self.callbacks.needShowFindLine(True)

    def newUpdateProgress(self, progress):
        if self.callbacks:
            self.callbacks.onNewUpdateProgress(progress)

    # @tryable
    # @by_timer(0.3)
    def close_app_now(self):
        self.MAY_CLOSE_NOW = True
        if self.callbacks:
            self.callbacks.onNeedCloseApp()

    def onGotChatUsersCall(self, users_checked):
        if self.callbacks != None:
            self.callbacks.gotChatUsersCallback(users_checked)

    def onNeedRegisterCall(self):
        if self.callbacks != None:
            self.callbacks.needRegisterCallback()

    def onLoginOccupiedCall(self):
        if self.callbacks != None:
            self.callbacks.needShowErrorCallback(ChatApiConsts.ERROR_LOGIN_OCCUPIED, "Cant register with this login.")

    def onApiClientOldCall(self):
        if self.callbacks != None:
            self.callbacks.needShowErrorCallback(ChatApiConsts.ERROR_API_CLIENT_OLD, "Application is too old. \nPlease install newer version.")

    def onApiServerOldCall(self):
        if self.callbacks != None:
            self.callbacks.needShowErrorCallback(ChatApiConsts.ERROR_API_SERVER_OLD, "Server application is too old. \nPlease ask your administrator to install newer version.")

    def onSendMessageCall(self):
        if self.callbacks != None:
            self.callbacks.closeResendWidget()

    def fileLoadProgress(self, fileId, progress, download=True): # FIXME
        if self.callbacks:
            self.callbacks.fileProgressCallback(fileId, progress, download)

    def raiseWindow(self):
        if self.callbacks:
            self.callbacks.needRaiseWindow()

    def gotServerSettings(self, d):
        if self.callbacks:
            self.callbacks.gotServerSettings(d)

    def onConnectedCall(self):
        if self.callbacks != None:
            self.callbacks.connectedCallback()

    def onChatsUpdatedListCall(self):
        if self.callbacks != None:
            self.callbacks.chatsUpdatedListCallback()

    def showChat(self, chat_id, chat_name=None):
        if self.callbacks:
            self.callbacks.needShowChat(chat_id, chat_name)

    def updateChatMessagesGui(self, withScrollToBottom=False):
        if self.callbacks:
            self.callbacks.messagesUpdateCallback(withScrollToBottom)

    def applyBadges(self):
        if self.callbacks:
            self.callbacks.needApplyBadges(self.badgeCount)

    def showError(self, text):
        if self.callbacks != None:
            self.callbacks.needShowErrorCallback(ChatApiConsts.ERROR_SIMPLE, text)

    @by_timer(1)
    def onGotAvatarCall(self):
        if self.callbacks != None:
            self.callbacks.gotAvatarCallback()

    def onCurrentUserProfileUpdatedCall(self):
        if self.callbacks != None:
            self.callbacks.updateNavigationDrawerCallback()

    def showNotify(self, noti_text, title=""):
        if self.callbacks:
            self.callbacks.needShowNotify(noti_text, title)

    def _showLastSmartInfo(self):
        if self.callbacks:
            keys = sorted(self._smart_info.keys())
            if len(keys) > 0:
                self.callbacks.needShowSmartInfo(self._smart_info.get(keys[-1]))
            else:
                self.callbacks.needShowSmartInfo(None)

    def onGotLoggedInSuccessCall(self):
        if self.callbacks:
            self.callbacks.gotLoggedInCallback()
            self.callbacks.gotConnectFinCallback()

    def onDisconnectedCall(self):
        if self.callbacks != None:
            self.callbacks.disconnectedCallback()

    def onNeedShowErrorCall(self):
        if self.callbacks != None:
            self.callbacks.needShowErrorCallback(ChatApiConsts.ERROR_NO_CONNECT, "No connect")

    def onLastVersionGreater(self, ver):
        if self.callbacks:
            self.callbacks.lastVersionGreater(ver)


class ChatApiConnect(ChatApiConsts, ChatApiConf, ChatApiDebug, ChatApiCallbacksPoint):
    connectedServer = None
    connectErrors = []
    servers = []
    _connected_ws = None
    doConnectStarted = None
    _is_disconnecting_now = False
    server_abils = None
    old_connect = False
    server_auth_ver = 0
    _is_connecting = None

    def init_connecting(self):
        self._is_connecting = set()
        self.connectedServer = set()

    def connect(self, name=None, pwd=None, register=False):
        self._is_connecting.clear()
        self._is_connecting.add(1)

        self._is_connecting.add(-1)
        self.disconnect(DISCONNECT_FOR_RECONNECT)

        self._login = name
        self._pwd = pwd
        self._register = register

        self.connectErrors = []
        self._websockets = {}

        self.parsers = {}
        self.parsers["connect"] = ConnectParser.ConnectParser()
        self.parsers["get_users_list"] = GetUsersListParser.GetUsersListParser()
        self.parsers["get_chats_list"] = GetChatsListParser.GetChatsListParser()
        self.parsers["get_users_avatar"] = GetUsersAvatarParser.GetUsersAvatarParser()
        self.parsers["common_data"] = CommonDataParser.CommonDataParser()
        self.parsers["get_profile"] = GetProfileParser.GetProfileParser()
        self.parsers['get_server_settings'] = GetServerSettingsParser.GetServerSettingsParser()
        self.parsers['get_server_info'] = GetServerInfoParser.GetServerInfoParser()
        #self.parsers["update"] = self.parsers["common_data"].getUpdateParser()

        self.started  = True
        self.savePrefs()

        self.users = {}
        self.lastMessages = []
        self.users_avatars = {}
        self.old_connect = False

        self.servers = []
        if len(self.serverAddress) > 1:
            self.servers.append(self.serverAddress)
        if self.useServer2 and self.serverAddress2 and len(self.serverAddress2) > 1:
            self.servers.append(self.serverAddress2)

        if len(self.servers) > 0:
            i = 0
            any_wrong = False
            for s in self.servers:
                self.debug("\tserver: " + s)

                wrong = False

                if s == None or s.count(":") > 1:
                    wrong = True
                else:
                    _lst = s.split(":")
                    lst = _lst[0].split(".")
                    if len(lst) != 4:
                        self.debug("\tserver wrong 1: " + str(len(lst)) + " / " + s)
                        wrong = True
                    else:
                        port_ok = True
                        if len(_lst) > 1:
                            try:
                                int(_lst[1])
                            except Exception:
                                port_ok = False

                        if port_ok:
                            for ss in lst:
                                if ss == None or len(ss) == 0:
                                    self.debug("\tserver wrong 2: " + ss)
                                    wrong = True
                                    break
                                val = -1
                                try:
                                    val = int(ss)
                                except Exception:
                                    pass

                                if val < 0 or val > 255:
                                    self.debug("\tserver wrong 3: " + str(val))
                                    wrong = True
                                    break

                if wrong and False:
                    any_wrong = True
                    if i == 0:
                        if self.callbacks != None:
                            self.callbacks.needShowErrorCallback(self.ERROR_WRONG_SERVER_1, "Wrong server 1")

                    elif i == 1:
                        if self.callbacks != None:
                            self.callbacks.needShowErrorCallback(self.ERROR_WRONG_SERVER_2, "Wrong server 2")
                    break

                i += 1

            if not any_wrong:
                self._is_connecting.add(2)
                self.do_connect_start(with_disconnect=False)

        else:
            if self.callbacks != None:
                self.callbacks.needShowErrorCallback(self.ERROR_NOSERVERS, "No servers")

    @in_thread
    def do_connect_start(self, with_disconnect=True):
        self.do_connect(with_disconnect=with_disconnect)

    def cleanUserConnect(self, type=DISCONNECT_FULL):
        self.users = {}
        self.chats[:] = []
        self.users_avatars = {}
        self.lastMessages = []
        self.current_chat_messages = CurrentChatMessages()

        self.is_admin = False

        self.user_id = None
        self.user_token = None
        self.server_uid = None
        self.current_chat_id = -1
        self.opening_chat_id = -1
        self.userProfile = None
        self.connectedServer.clear()
        self.currentServer = -1

        self.badgeCount = 0

        if type != DISCONNECT_FOR_RECONNECT:
            self._login = None
            self._pwd = None

        self.creatingChat = None
        self.createdFile = None

        self.user_type = None
        self.resendMessage = None

        self.filesProgresses = {}
        self.last_chat_id = -1
        self.last_chat_id_for_scroll = -1
        self._getting_last_messages = None

        self.doConnectStarted = None
        self._smart_info = {}
        self._smart_info_id = 0

        self.mouse_pos_change_control.set_sended(False)

        if self.callbacks != None:
            self.callbacks.messagesUpdateCallback(None)

        if self.callbacks != None:
            self.callbacks.needCloseAllOpenedWindows()

    @tryable
    def do_connect(self, with_disconnect=True):

        if with_disconnect:
            self._is_connecting.add(-2)
            self.disconnect(DISCONNECT_FOR_RECONNECT)

        futures = []
        for server in self.servers:
            futures.append(self.connect_api_auth(server)) #self.make_ws_app(server=server)

        while True:
            sm = sum(fu.state for fu in futures)
            if sm >= len(futures):
                break
            sleep(0.3)

    @in_thread # FIXME
    def connect_api_auth(self, server):
        self._is_connecting.add(3)

        device_id = getDeviceId()
        print('[ connect_api_auth ]', device_id)

        headers = {}
        if self._login and self._pwd:
            if self.server_auth_ver < 1:
                self.old_connect = True
                self.make_ws_app(server, uid=device_id)
                return
            else:
                headers['Authorization'] = '{}={}'.format(self._login, md5Apache(self._pwd))
                headers['is_register'] = "1" if self._register else "0"

        http = 'https'
        if ":" not in server:
            server += ":8887"
        else:
            if isUrlHttp(server):
                http = 'http'
        self.http = http

        print('[ connect_api_auth ] 2')

        url = http + '://' + server + '/api/connect/?can=parts&uid=' + device_id
        r = self.r_connect(url, headers, 1)
        if not r:
            return

        print('[ connect_api_auth ] 3:', r.status_code)

        if r.status_code == 401:
            no_401 = r.json().get('auth') == 'no'
            print('[ connect_api_auth ] 401 auth=no:', no_401)
            headers = {}
            if no_401:
                r = self.r_connect(url, headers, 2)
                if not r:
                    print('  -> return')
                    return

        elif r.status_code == 404:
            print('[ connect_api_auth ] 404 return', device_id)
            self.old_connect = True
            self.make_ws_app(server, uid=device_id)
            return

        if r.status_code not in (200, 401):
            print('[ connect_api_auth ] UNKNOWN status_code:', r.status_code)
            return

        self._is_connecting.add(4)

        try:
            start = datetime.now()
            print('[ connect_api_auth ] connected ', start)
            #data = r.json() if r.status_code in (200, 401) else None
            c_c = 0
            for data in self.r_get_json(r):
                c_c +=1
                if len(data) > 2:
                    print('[data:{}:{}]'.format(len(data), c_c), end='')
                else:
                    print('.', end='')

                if data and data.get('auth') == 'no_uid':
                    print('\n[ connect_api_auth ] no_uid')
                    server_uid = data.get('server')
                    if server_uid:
                        self.init_connect(server_uid)
                        self.load_user_token()
                        if self.user_token:
                            headers = {}
                            url += '&utkn={}'.format(self.user_token)
                            r = self.r_connect(url, headers, 2)
                            if not r:
                                return
                            if r.status_code not in (200, 401):
                                self._is_connecting.add(-50)
                                self._is_connecting.discard(4)
                                return
                            data = r.json() if r.status_code in (200, 401) else None

                if data and data.get('auth') == 'no_uid':
                    print('\n[ connect_api_auth ] no_uid: onNeedRegister')
                    self.onNeedRegister(data.get('auth_ver', 0))
                    return

                if data and r.status_code == 200:
                    print('\n[ connect_api_auth ] status_code ==> 200')

                    if 'token' in data and 'id' in data:

                        self.connectedServer.add(server)

                        add = ''
                        server_uid = data.get('server', None)
                        abils = data.get('abils')

                        if server_uid:
                            add += ' server:{}'.format(server_uid)
                        else:
                            server_uid = 'old_server'

                        self.init_connect(server_uid)
                        self.setServerUid(server_uid)
                        self.setUserAndToken(
                            data["token"],
                            data["id"]
                        )
                        self.save_connect()

                        self.setIsAdmin(False)
                        self.setAbils(abils)

                        self.onConnectedCall()
                        self.make_ws_app(server, uid=device_id)

                    if 'admin' in data:
                        is_admin = data.get('admin', False)
                        add = ' ADMIN user' if is_admin else ' OTHER user'
                        self.setIsAdmin(is_admin)

                    if 'users' in data:
                        self.parsers["get_users_list"].parseUsersJson(data['users'])

                    if 'groups' in data:
                        self.parsers["get_chats_list"].parserGroupsJson(data['groups'])

                    if 'photos' in data:
                        self.parsers["get_users_avatar"].parseUsersAvatars({k:v for k,v in data["photos"]})
                        self.startLoadUsersAvatars()

                    if 'profile' in data:
                        self.parsers["get_profile"].got_user_profile(data["profile"])

        except urllib3.exceptions.ReadTimeoutError:
            print('[ connect_api_auth ] ReadTimeoutError')
            self.r_err_clear(server, -30)

        except BaseException:
            print('[ connect_api_auth ] BaseException')
            self.r_err_clear(server, -100)
            raise

        end = datetime.now()

    def r_err_clear(self, server, err_num, with_close=True):
        self._is_connecting.add(err_num)
        self._is_connecting.discard(4)
        self.connectedServer.discard(server)
        w = self._websockets.get(server, None)
        if w:
            del self._websockets[server]
            while w in self.ws_apps:
                self.ws_apps.remove(w)
            if with_close:
                w.close()

    def r_connect(self, url, headers, num):
        try:
            return requests.get(url, timeout=30, verify=False, headers=headers, stream=True)
        except BaseException as e:
            print('[ r_connect ERR ]', e)
            return

    def r_get_json(self, r):
        data = b''
        while True:
            raw = r.raw.read(128)
            if not raw:
                return
            data += raw
            try:
                if data.strip().endswith(b'}'):
                    jsn_data = data.decode('utf-8')
                    jsn = json_loads(jsn_data) #, encoding='utf-8')
                    data = b''
                else:
                    jsn = {}
            except Exception as e:
                print('<data> E:', e)
                jsn = {}
            yield jsn

    @tryable
    def make_ws_app(self, server, uid=None):
        _add = ''
        _ver = self.CLIENT_API_VERSION
        if self.app_version:
            _ver = self.app_version
        if _ver:
            _add = '&version={}'.format(_ver)
        if uid:
            _add += '&uid=' + uid
        if self.auth_hidden:
            _add += '&hidden=true'

        wss = "wss"
        if ":" not in server:
            server += ":8887"
        else:
            if isUrlHttp(server):
                wss = 'ws'
        self.wss = wss

        _wss_url = wss + "://" + server + '/wapi/connect/?platform=win64' + _add

        w = WebSocketApp(_wss_url,
                         on_message=lambda ws, data: self._on_message(ws, data),
                         on_error=lambda ws, err: self._on_error(ws, err),
                         on_close=lambda ws: self._on_close(ws, w))

        self._websockets[server] = w
        self.ws_apps.append(w)

        if self.old_connect:
            w.on_open = lambda ws: self._on_open(ws)
        else:
            w.on_open = lambda ws: self._on_open_new(ws)

        @in_thread
        def w_run_forever():
            w.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        w._w_run_forever = w_run_forever
        w_run_forever()

    @tryable
    def disconnect(self, type=DISCONNECT_FULL):
        if type != DISCONNECT_FOR_RECONNECT:
            self.started = False
            self.connectedServer.clear()

        if type == DISCONNECT_FULL:
            self.savePrefs()

        self._do_disconnect()
        self.cleanUserConnect(type)

    @tryable
    def _do_disconnect(self):
        ws_apps = copy(self.ws_apps)
        if not len(ws_apps):
            return

        with self.disconnecting():
            for wa in ws_apps:
                wa.close()

    @contextmanager
    def disconnecting(self):
        self._is_disconnecting_now = True
        try:
            yield
        finally:
            self._is_disconnecting_now = False

    def disconnectOnce(self):
        self.disconnect(DISCONNECT_ONCE)

    def disconnectForReconnect(self):
        self.disconnect(DISCONNECT_FOR_RECONNECT)

    def onNeedRegister(self, auth_ver=0):
        self.debug(f"onNeedRegister: {auth_ver}")

        self.server_auth_ver = auth_ver

        self.onNeedRegisterCall()

        self.disconnect(DISCONNECT_ONCE) # FIXME different disconnect!

    @tryable
    def _on_open_new(self, ws, *args):

        self._connected_ws = ws

        self.setCurrentServerFromUrl(ws.url)

        self.onGotLoggedInSuccessCall()

    @tryable
    def _on_open(self, ws, *args):
        self._connected_ws = ws

        self.setCurrentServerFromUrl(ws.url)

        self.onConnectedCall()

        if self._login:
            pass

        if self._login != None and self._pwd != None:
            self.startRegister()
        else:
            d = {
                "uuid": getDeviceId(),
                "version": self.CLIENT_API_VERSION
            }
            if self.auth_hidden:
                d["hidden"] = True
            self.send(url="/users/auth/", attrs=d)

    @tryable
    def _on_close(self, ws, w_app, *args):
        if not w_app:
            w_app = ws

        if w_app in self.ws_apps:
            self.ws_apps.remove(w_app)

        sock = w_app.sock if w_app else None
        code = sock.status if sock else None

        if self._connected_ws == ws:
            self._connected_ws = None

        if code == 101 and not self._is_disconnecting_now:
            self.cleanUserConnect(DISCONNECT_FULL)

            self.onDisconnectedCall()

    @tryable
    def _on_error(self, ws, err):
        server = None
        for _server, _ws in self._websockets.items():
            if ws == _ws:
                server = _server
        if server:

            is_current = self.isConnectedOrConnectedNull(server)
            if is_current and self.started:

                self.mouse_pos_change_control.set_sended(False)

                if self.addConnectError(server):
                    self.showError("No connect...")
                else:
                    self.showError("Reconnect...")

                self.setCurrentServerFromUrl(None)
                self.doConnectStarted = None

                #del self._websockets[server]
                self.r_err_clear(server, -101, with_close=False)

    def startRegister(self):
        login = self._login
        pwd = self._pwd
        self._login = None
        self._pwd = None
        self.send(url="/users/auth/register/", attrs={
            "uuid": getDeviceId(),
            "login": login,
            "password": md5Apache(pwd),
            "version": self.CLIENT_API_VERSION,
            "is_register": self._register
        })

    def addConnectError(self, errorUrl):
        self.connectErrors.append(errorUrl)
        if len(self.connectErrors) >= len(self.servers):
            self.onNeedShowErrorCall()
            return True
        return False

    def _on_message(self, ws, data):
        pass

    def send(self, url, attrs, debug=True):
        pass

    def startLoadUsersAvatars(self):
        if not self.with_users or not self.with_avatars:
            return
        for user in self.users.values():
            photo_id = user.profile.getPhotoId()
            if len(photo_id) > 0:
                # FIXME
                fileLoader = FileLoader(photo_id, "")
                fileLoader.executeOnExecutor()

    #--------------------------------------------------------

    def setIsAdmin(self, value):
        self.is_admin = value

    def setAbils(self, abils):
        self.server_abils = abils

    def is_connected(self):
        return len(self.connectedServer) > 0

    def is_connecting_good(self):
        return 4 in self._is_connecting

    def isConnectedOrConnectedNull(self, server):
        if not self.connectedServer:
            return True
        for s in self.connectedServer:
            if s.startswith(server):
                return True
        return False

    def getCurrentServerAddress(self):
        if self.getCurrentServer() == 0:
            server = self.serverAddress
        else:
            server = self.serverAddress2
        return self.getFullServerAddress(server)

    def getCurrentServer(self):
        if self.currentServer > 0 and self.useServer2:
            return 1
        return 0

    def setCurrentServerFromUrl(self, url):
        if url == None:
            self.connectedServer.clear()
            return

        self.connectedServer.add(self.serverFromUrl(url))
        self.currentServer = 0
        if self.useServer2:
            if self.serverAddress2 and len(self.serverAddress2) > 0 and self.serverAddress2 in url:
                self.currentServer = 1

    def serverFromUrl(self, url):
        if self.serverAddress and len(self.serverAddress) > 0 and self.serverAddress in url:
            return self.getFullServerAddress(self.serverAddress)
        if self.serverAddress2 and len(self.serverAddress2) > 0 and self.serverAddress2 in url:
            return self.getFullServerAddress(self.serverAddress2)
        return None

    @staticmethod
    def getFullServerAddress(server):
        server = server.replace(" ", "").lower().replace("http://", "").replace("https://", "").replace("wss://", "").replace("ws://", "")
        if ":" not in server:
            server += ":8887"
        return server