import sys
from time import sleep

def do_api(tunes):
    # start_task=CONTENT,STR(ID),AUTOR,LOGIN_EX,LOGIN_RE

    for i, a in enumerate(sys.argv):
        if a.startswith('start_task='):
            a = ' '.join(sys.argv[i:])
            args = a[len('start_task='):].split(',')
            org_task(args)
            break

        elif a == 'find_me':
            find_me()

        elif a == 'get_last_version':
            get_last_version()

        elif a == 'try_update':
            try_update()

        elif a == 'tst_updater':
            tst_updater()

        elif a == 'send_version':
            send_version()


def find_me():
    from bp_chat.logic.common.sub import find_my_sub
    find_my_sub()

def get_last_version():
    from bp_chat.logic.chat_api.ChatApi import ChatApi

    ChatApi.instance(need_work=False, update_local_path=_get_update_path()).getLastVersion()

def try_update():
    from bp_chat.logic.chat_api.ChatApi import ChatApi
    ChatApi.instance(need_work=False, update_local_path=_get_update_path()).start_update_clicked()

def _get_update_path():
    update_local_path = None
    for a in sys.argv:
        if a.startswith('update_path='):
            update_local_path = a[len('update_path='):]
    return update_local_path

def org_task(args):

    from bp_chat.logic.chat_api.ChatApi import ChatApi, ChatApiCallbacksClean
    chat_api = ChatApi.instance(
        with_thread=False,
        with_avatars=False,
        with_groups=False,
        with_users=False,
        auth_hidden=True,
        with_logger=False
    )

    _Closer = {
        'fin': False,
        'open_chat_id': None
    }

    class _Callbacks(ChatApiCallbacksClean):

        def gotLoggedInCallback(self):
            chat_api.send(url="/org/task/", attrs={
                'content':args[0],
                'id':args[1],
                'author':args[2],
                'login_ex':args[3],
                'login_re':args[4],
                'executors':args[5:]
            })

        def gotUsersListCallback(self, users):
            pass

        def needShowChat(self, chat_id, chat_name):
            _Closer['open_chat_id'] = chat_id
            if _Closer['open_chat_id'] != None and _Closer['open_chat_id'] >= 0:
                _Closer['fin'] = True

    chat_api.connect_callbacks(_Callbacks())

    chat_api.connect()

    for i in range(5):
        if _Closer['fin']:
            break
        sleep(1)

    from bp_chat.logic.common.sub import find_my_sub, start_sub
    found = find_my_sub()
    if found == None:
        add = ''
        for a in sys.argv:
            if a.startswith('UID_SUF='):
                add += ' ' + a
        if 'nolog' in sys.argv:
            add += ' nolog'
        if 'debug' in sys.argv:
            add += ' debug'

        start_sub("open_chat={}{}".format(_Closer['open_chat_id'], add))
        sleep(2)

    sys.exit(0)


def tst_updater():
    # from .logic.file_load.Updater import Updater
    # Updater.update_updater()
    pass

def send_version():

    from bp_chat.logic.chat_api.ChatApi import ChatApi, ChatApiCallbacksClean
    chat_api = ChatApi.instance(
        with_thread=False,
        with_avatars=False,
        with_groups=False,
        with_users=False,
        auth_hidden=True,
        with_logger=False
    )

    _Closer = {
        'fin': False,
        #'open_chat_id': None
    }

    class _Callbacks(ChatApiCallbacksClean):

        def gotLoggedInCallback(self):
            chat_api.setCurrentChatId(43)
            text = r'New version at: K:\BP_CHAT\BP Chat\bp_chat.exe'
            if 'jk' in sys.argv:
                text = r'New version at: K:\BP_CHAT\JK\for-testing\app-release.apk'
            chat_api.sendMessage(text)
            _Closer['fin'] = True

        def gotUsersListCallback(self, users):
            pass

        def messagesUpdateCallback(self, withScrollToBottom=False):
            #_Closer['open_chat_id'] = chat_api.getCurrentChatId()
            # if _Closer['open_chat_id'] != None and _Closer['open_chat_id'] >= 0:
            #     _Closer['fin'] = True
            pass

    chat_api.connect_callbacks(_Callbacks())

    chat_api.connect()

    for i in range(5):
        if _Closer['fin']:
            sleep(2)
            break
        sleep(1)

    sys.exit(0)