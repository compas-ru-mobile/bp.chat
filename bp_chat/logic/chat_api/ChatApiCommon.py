
import hashlib
import traceback, sys
import os
from os.path import expanduser, join, exists, dirname, basename
from datetime import datetime
from threading import Thread, Timer

from bp_chat.logic.common.app_common import get_app_dir_path, APP_NAME_DIR, with_uid_suf
from bp_chat.logic.common.log import get_stdout_real

if 'api' not in sys.argv:
    from PyQt5.QtGui import QIcon, QColor, QCursor # FIXME

def color_from_hex(hex_color):
    hex_color = hex_color.replace("#", "")
    lst = [ int(hex_color[i*2:i*2+2], 16) for i in range(3) ]
    return QColor(*lst)

if 'api' not in sys.argv:
    COLOR_MY_MESSAGE = color_from_hex("#eeeeee") #color_from_hex("#e7f9e7")
    COLOR_MESSAGE_NOT_READED = color_from_hex("#fae0c6")
    COLOR_MESSAGE_CLEAN = color_from_hex("#ffffff")

# try:
#     from colorama import init
#     from termcolor import colored
#     init()
# except ImportError:
colored = lambda s, *args: s

ALPHAVET_SIMPLE = 'QWERTYUIOPASDFGHJKLZXCVBNM' + 'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЁ'
ALPHAVET_SIMPLE += ALPHAVET_SIMPLE.lower() + '1234567890-=_+!@#№$%^&*()~`[]{};:\'"\\|,<.>/?\n\t '
SMILES = '😁😊🤔🤣👍🥳😳🤫😢😉😡🥴🤦🤨👏😱😭😀'
ALPHAVET_FULL = SMILES + ALPHAVET_SIMPLE

SMILES_DICT = {
    '😢': 'smile_1',
    '😁': 'smile_2',
    '😊': 'smile_3',
    '🤔': 'smile_4',
    '🤣': 'smile_5',
    '👍': 'smile_6',
    '🥳': 'smile_7',
    '😳': 'smile_8',
    '🤫': 'smile_9',
    # '😢':,
    '😉': 'smile_10',
    '😡': 'smile_11',
    '🥴': 'smile_12',
    '🤦': 'smile_13',
    '🤨': 'smile_14',
    '👏': 'smile_15',
    '😱': 'smile_16',
    '😭': 'smile_17',
    '😀': 'smile_18',
}


class CHAT_API_ENUMS:
    FILE_DOWNLOAD = 1
    FILE_DOWNLOAD_AVATAR = 2
    FILE_UPLOAD = 3

    JPEG_FILE_PREFIX = "img"
    JPEG_FILE_SUFFIX = ".jpg"

def isUrlHttp(serverAddress):
    return serverAddress.endswith(":8000") or serverAddress.endswith(":8080")

def doNotify(noti_text, title=""):
    from .ChatApi import ChatApi
    chatApi = ChatApi.instance()
    chatApi.showNotify(noti_text, title)


def md5Apache(pwd):
    m = hashlib.md5()
    m.update(pwd.encode('utf-8'))
    return m.hexdigest().upper()

from bp_chat.core.tryable import tryable


def is_win():
    return sys.platform.startswith('win')

def is_osx():
    return sys.platform == 'darwin'


if is_win():

    from bp_chat.logic.common import uniq

    def getDeviceId_2(first_start=False):
        if first_start:
            getDeviceId_2.__uuid = with_uid_suf(uniq.Uniqizer().all_id('-'))
        ret = getDeviceId_2.__uuid
        return ret

else:
    if is_osx():
        from plyer.platforms.macosx import uniqueid as _uniqueid
        uniqueid = _uniqueid.instance()
        _get_u_id = lambda: uniqueid.id
    else:
        from plyer import uniqueid
        _get_u_id = lambda: uniqueid.id

    def getDeviceId_2(first_start=False):
        id = _get_u_id()

        _username = basename(expanduser('~'))

        id = md5Apache(id.decode('utf-8') + "-" + _username)
        i = 0
        id2 = ''
        for a in id:
            id2 += a
            if i > 7:
                id2 += "-"
                i = -1
            i += 1

        return with_uid_suf(id2)

def getDeviceId(first_start=False):
    if hasattr(setDevId, 'val'):
        return setDevId.val
    ret = getDeviceId_2(first_start)
    return ret

def setDevId(val):
    setDevId.val = val


IN_THREAD_INITED = -1
IN_THREAD_STARTED = 0
IN_THREAD_FINISHED = 1


class Future:
    state = IN_THREAD_INITED


def in_thread(func):

    def _func(*args, **kwargs):
        future = kwargs.pop('future')
        future.state = IN_THREAD_STARTED

        try:
            func(*args, **kwargs)
        except BaseException as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            formatted_lines = traceback.format_exc().splitlines()

            fexc = traceback.format_exception(exc_type, exc_value,
                                            exc_traceback)

            fe_line = ''.join(fexc[2:])
            if ', line' not in fe_line:
                fe_line = ''.join(fexc)

        future.state = IN_THREAD_FINISHED

    def _new_func(*args, **kwargs):
        future = Future()
        kwargs['future'] = future

        thread = Thread(target=_func, args=args, kwargs=kwargs)
        thread.daemon = True
        _new_func.thread = thread
        _new_func.future = future
        thread.start()

        return future

    _new_func.future = Future

    return _new_func


def by_timer(seconds, on_finish=None):
    def _new_decorator(func):
        def _new_func_do(*args, **kwargs):
            ret = func(*args, **kwargs)
            if on_finish:
                on_finish(*args, **kwargs)
            return ret
        def _new_func(*args, **kwargs):
            if hasattr(_new_func, 'timer') and _new_func.timer:
                _new_func.timer.cancel()
                del _new_func.timer
                _new_func.timer = None
            timer = Timer(seconds, _new_func_do, args=args, kwargs=kwargs)
            _new_func.timer = timer
            timer.start()
        return _new_func
    return _new_decorator


# def once_in_seconds(seconds):
#     def _new_decorator(func):
#         def _new_func(*args, **kwargs):
#             if hasattr(_new_func, 'once_in_seconds_timer') and _new_func.timer:
#                 _new_func.once_in_seconds_timer.cancel()
#                 _new_func.once_in_seconds_timer = None
#             timer = Timer(seconds, func, args=args, kwargs=kwargs)
#             _new_func.once_in_seconds_timer = timer
#             timer.start()
#         return _new_func
#     return _new_decorator



def loadAvatarFromAppDir(fileName):

    filepath = join(get_avatars_dir_path(), fileName)
    if not exists(filepath):
        return None

    return QIcon(filepath)


def saveAvatarToAppDir(fileName, data):
    avatars_dir_path = get_avatars_dir_path()

    if not exists(avatars_dir_path):
        try:
            os.makedirs(avatars_dir_path)
        except:
            pass

    filepath = join(avatars_dir_path, fileName)
    with open(filepath, 'wb') as f:
        f.write(data)


def get_avatars_dir_path():
    return join(get_app_dir_path(), with_uid_suf('.chat'), 'avatars')

# def get_files_db_path():
#     return join(get_app_dir_path(), with_uid_suf('.chat'), 'files.db')

def get_server_data_path(server_uid):
    return join(get_app_dir_path(), with_uid_suf('.chat'), 'srv', server_uid)



def openInputStream_from_ContentResolver(uri):
    filename = uri
    return open(filename, 'rb')


#@ApiObject.init_ProgressNotify
class ProgressNotify:

    def __init__(self, fileName, type):
        self.fileName = fileName
        self.type = type
        from .ChatApi import ChatApi
        self.chatApi = ChatApi.instance()
        self.text_format = "Sending file{}" if type == CHAT_API_ENUMS.FILE_UPLOAD else "Downloading file{}"
        self.smartInfoId = self.chatApi.addSmartInfo(self.text_format.format(""))

    def updateProgress(self, progres):
        self.chatApi.showSmartInfo(self.smartInfoId, self.text_format.format(": " + str(progres) + "%"))

    def finish(self, success, cancelled):
        self.chatApi.delSmartInfo(self.smartInfoId)


from bp_chat.core.local_db_files import getDownloadsFilePath, getDownloadsDirectoryPath, get_files_db_path



def updateNotiByBadges(): # FIXME it is not needed in windows version... hmm ... or needed something else?
    from .ChatApi import ChatApi
    chatApi = ChatApi.instance()
    if chatApi.callbacks:
        chatApi.callbacks.chatsUpdatedListCallback()


def createImageFileName():
    imageFileName = CHAT_API_ENUMS.JPEG_FILE_PREFIX + "{:%Y%m%d_%H%M%S}".format(datetime.now()) + CHAT_API_ENUMS.JPEG_FILE_SUFFIX
    return join(getDownloadsDirectoryPath(), imageFileName)


def getGlobalMousePos():
    try:
        pos = QCursor.pos()
        w, h = pos.x(), pos.y()
    except:
        w = h = -1
    return w, h


class ChangeControl:

    def __init__(self, change_timout, init_obj=None):
        self.change_timout = change_timout
        self.last_time = None
        self.last_obj = init_obj
        self.current_state = None
        self.sended = False

    def check_new_value_changed(self, new_obj):

        new_state = self._check_is_other_value_or_in_timeout(new_obj)

        if new_state != self.current_state:
            self.current_state = new_state
            self.sended = False
            return new_state

    def _check_is_other_value_or_in_timeout(self, new_obj):

        if self.is_other_value(new_obj):
            self.mem_value_change(new_obj)
            return True

        if self.is_in_timout():
            return True

        return False

    def is_other_value(self, new_obj):
        return new_obj != self.last_obj or not self.last_time

    def mem_value_change(self, new_obj):
        self.last_obj = new_obj
        self.last_time = datetime.now()

    def is_in_timout(self):
        return (datetime.now() - self.last_time).total_seconds() < self.change_timout

    def clear_current_state(self):
        self.current_state = None

    def is_sended(self):
        return self.sended

    def set_sended(self, val=True):
        self.sended = val

    def get_current_state(self):
        return self.current_state

