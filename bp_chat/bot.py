import sys, os
from os.path import abspath, join, dirname, exists, basename
from time import sleep
from threading import Timer
from random import randint

HERE = dirname(abspath(__file__))
PROJ_PATH = dirname(HERE)
PROJS_PATH = dirname(dirname(PROJ_PATH))

from .logic.chat_api.ChatApi import ChatApi, ChatApiCallbacksClean
from .logic.chat_api.ChatApiCommon import setDevId


def checkable(func):
    func.checkable = True
    return func


class ChatBot(ChatApiCallbacksClean):

    check = {}

    def __init__(self, uuid, server_address):

        if uuid:
            setDevId(uuid)

        need_my_messages = getattr(self, 'need_my_messages', False)

        self.chat_api = ChatApi.instance(
            may_save_load_prefs=False,
            with_thread=True,
            with_avatars=False,
            with_groups=True,
            with_users=True,
            auth_hidden=False,
            with_logger=False,
            need_check_update=False,
            may_send_active=False,
            need_my_messages=need_my_messages
        )
        self.chat_api.serverAddress = server_address
        self.chat_api.useServer2 = False
        self.chat_api.connect_callbacks(self)

        ChatApiCallbacksClean.__init__(self.chat_api)

        self.funcs = {}
        for name in dir(self):
            if name.startswith('do_'):
                func = getattr(self, name)
                nm = name[3:]
                _checkable = getattr(func, 'checkable', False)
                self.funcs[nm] = (func, _checkable)

    def connect(self):
        self.chat_api.connect()

    def needRegisterCallback(self):
        self.t = Timer(3, self._do_register)
        self.t.daemon = True
        self.t.start()

    def _do_register(self):
        if not self.login or not self.pwd:
            return
        #self.chat_api.connect(name=self.login, pwd=self.pwd, register=True) #, register='one_register' in sys.argv)

    def gotUsersListCallback(self, users):
        user = self.chat_api.getCurrentUser()
        self.chat_api.sendActive(True, True)

    def onMessageCallback(self, message):
        text = message.text.strip() if message else '-'
        chat_id = message.chat_id if message else None
        if text.startswith('\\'):

            for name, (func, _checkable) in self.funcs.items():
                nm = '\\{}'.format(name)
                boo = text.startswith(nm)
                if boo:
                    _txt = text[len(nm):]
                    if len(_txt) and _txt[0] not in ' :':
                        boo = False
                if boo:
                    if _checkable:
                        self.prepare_do(chat_id, name)
                    else:
                        getattr(self, 'do_' + name)(chat_id, self.prepare_args(text))
                    break

        else:
            check = self.check.get(chat_id)
            if check and check['code'] == text:

                self.check.pop(chat_id)
                if check['name'] == 'on_not_command':
                    self.on_not_command(chat_id, check.get('args'))
                else:
                    func_name = "do_" + check['name']
                    func = getattr(self, func_name, None)
                    if func:
                        func(chat_id, check.get('args'))
            else:
                if getattr(self.on_not_command, 'checkable', False):
                    self.prepare_do(chat_id, 'on_not_command', message)
                else:
                    self.on_not_command(chat_id, message)

    def on_not_command(self, chat_id, message):
        pass

    def prepare_do(self, chat_id, name, args=None):
        self.chat_api.setCurrentChatId(chat_id)
        code = ''.join(str(randint(0, 9)) for _ in range(4))
        self.check[chat_id] = {
            'name': name, 'code': code, 'args': args
        }
        text = self.make_code_phrase(name, code, args)
        if text == None:
            return
        self.chat_api.sendMessage(text)

    def make_code_phrase(self, name, code, args):
        return "For '{}', please send me code: {}".format(name, code)

    def prepare_args(self, text):
        return text.strip().split(" ")[1:]

    def do_help(self, chat_id, args):
        coms = [ a[len('do_'):] for a in dir(self) if a.startswith('do_') ]
        self.chat_api.setCurrentChatId(chat_id)
        self.chat_api.sendMessage("{} commands:\n    {}".format(self.chat_api.getCurrentUserLogin(), '\n    '.join(coms))) #

    def set_INITIAL_FILES_DIR(self, p):
        if not exists(p):
            os.makedirs(p)
        from bp_chat.core.local_db_files import set_INITIAL_FILES_DIR
        set_INITIAL_FILES_DIR(p)

