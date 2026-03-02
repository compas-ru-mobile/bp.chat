import sys

from PyQt5.QtWidgets import QApplication, QPushButton, QSystemTrayIcon
from PyQt5.QtGui import QIcon

from bp_chat.gui.ui import res
from bp_chat._tune import Tunes
from bp_chat.gui.MainWidget import MainWidget
from bp_chat.logic.chat_api.ChatApi import ChatApi
from bp_chat.logic.chat_api.ChatApiCommon import tryable
from bp_chat.logic.common.log import set_print_log


class App(QApplication):

    def __init__(self, argv):
        super().__init__(argv)

    def event(self, e):
        return super().event(e)


@tryable
def main(*args):
    # if "nolog" not in sys.argv:
    #     sys.argv[1:2] = ["nolog"] + sys.argv[1:2]
    # if "debug" not in sys.argv:
    #     sys.argv[1:2] = ["debug"] + sys.argv[1:2]

    # if 'nolog' not in sys.argv:
    #     set_print_log(True)
    print('[ main ] starting...')
    print(sys.version)

    chatApi = ChatApi.instance(sys.argv)
    chatApi.set_app_version(Tunes.version)

    open_chat_id = None
    for a in sys.argv:
        if a.startswith('open_chat='):
            a = a[len('open_chat='):]
            try:
                open_chat_id = int(a)
            except BaseException as e:
                print('[error] {}'.format(e))

    app = App(sys.argv)

    w = MainWidget(app)
    w.set_app_tunes(Tunes)

    if open_chat_id != None:
        w.set_open_chat_id(open_chat_id)

    print('[ main ] showing...')
    w.show()

    ret = _exec(app)
    chatApi.finish()

    if ret == None:
        ret = -1

    try:
        sys.exit(ret)
    except:
        pass

@tryable
def _exec(app):
    return app.exec_()