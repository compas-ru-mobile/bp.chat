import sys
from os.path import abspath, join, dirname, exists
from time import sleep
from threading import Timer, Thread

HERE = dirname(abspath(__file__))
PROJ_PATH = dirname(HERE)
USER = HERE.replace('\\','//').split('/')[2]

sys.path.append(PROJ_PATH)
if 'api' not in sys.argv: # FIXME
    sys.argv.append('api')

from bp_chat.logic.chat_api.ChatApi import ChatApi, ChatApiCallbacksClean
from bp_chat.logic.chat_api.ChatApiCommon import setDevId


class _Callbacks(ChatApiCallbacksClean):

    check = {}

    # def gotLoggedInCallback(self):
    #     #print('---loggedIn---')
    def needRegisterCallback(self):
        print('[ need register ]')
        # self.t = Timer(3, self._do_register)
        # self.t.daemon = True
        # self.t.start()

    def _do_register(self):
        print('[do_register]')
        self.chat_api.connect(name='jk_bot', pwd=get_chat_unique(1), register=False)

    def gotUsersListCallback(self, users):
        print('---got_users:{}---'.format(list(users.keys())))
        user = self.chat_api.getCurrentUser()
        print('  me: {}'.format(user.name if user else '-'))
        #self.chat_api.sendActive(True, True)
        self._thread = Thread(target=self._sending_active)
        self._thread.daemon = True
        self._thread.start()

    def _sending_active(self):
        boo = False
        while True:
            sleep(5)
            boo = not boo
            self.chat_api.sendActive(boo, True)

    # def messagesUpdateCallback(self, withScrollToBottom):
    #     #print('---messagesUpdateCallback---')


def get_chat_unique(num):
    return open('build/chat_unique.txt', encoding='utf-8').read().split('|')[num].strip()

class ChatBot:

    def __init__(self):
        if exists('build/chat_unique.txt'):
            print('[ SET ] id')
            setDevId(get_chat_unique(0).encode('utf-8'))

        self.chat_api = ChatApi.instance(
            may_save_load_prefs=False,
            with_thread=True,
            with_avatars=False,
            with_groups=True,
            with_users=True,
            auth_hidden=False,
            with_logger=False,
            need_check_update=False,
            may_send_active=False
        )
        self.chat_api.serverAddress = '127.0.0.1'
        self.chat_api.useServer2 = False
        self.chat_api.connect_callbacks(_Callbacks(self.chat_api))

    def connect(self):
        self.chat_api.connect()



if __name__=='__main__':
    cb = ChatBot()
    cb.connect()
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        pass
    print('-' * 10 + "fin")