
import shutil
from threading import Thread
import requests
from os.path import exists, dirname, abspath, join
from os import makedirs
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
from zipfile import ZipFile
from subprocess import Popen, check_output, DEVNULL
import sys, os
from time import sleep

from bp_chat.logic.common.processes import is_in_python
from bp_chat.logic.common.app_common import get_to_app_dir_path


class Updater:

    _thread = None
    _update_data = None
    _update_path = "tmp/update"

    def __init__(self, chat_api):
        self.chat_api = chat_api

    def check_update_local(self):
        if exists(self._update_path):
            self.chat_api.newUpdateProgress(100)
            return

    @classmethod
    def start_updater(cls, exe_dir=None):
        exe_name = "Uninstall.exe"
        if not exe_dir:
            from bp_chat.logic.common.app_common import get_app_dir_path
            _p = get_app_dir_path()
            _to_dir = join(_p, "loaded")
            _to_updater_path = join(_to_dir, exe_name)
            if exists(_to_updater_path):
                exe_dir = _to_dir
            else:
                exe_dir = get_to_app_dir_path()
        exe_path = join(exe_dir, exe_name)
        if not exists(exe_path):
            return -1, "Not found on start updater"
        com = exe_path.replace('/', '\\') + " -install -start" #+ " -install -start" # -silent -update
        if "-install_from_testing" in sys.argv:
            com += " -install_from_testing"
        # if "args" in kwargs:
        #     com += " " + kwargs["args"]
        try:
            Popen(com, stdin=DEVNULL, stderr=DEVNULL, stdout=DEVNULL)
        except:
            return -2, "Cant start updater"
        return 0, None

    @classmethod
    def load_updater_version(cls):
        try:
            com = "https://bp.compas.ru/rapi/last_version/?app=chat-win-webinst"
            # if "-install_from_testing" in sys.argv:
            #     com += "&type=testing"
            r = requests.get(com, timeout=10)
        except BaseException:
            return ""
        new_version = r.text.strip()
        return new_version

    @classmethod
    def download_updater(cls, to_path):
        import urllib.request
        try:
            url = "https://bp.compas.ru/pres/bp_chat/win/bp_chat_web_installer.exe"
            urllib.request.urlretrieve(url, to_path)
        except BaseException:
            return None
        return True

    @classmethod
    def get_updater_version(cls, exe_path):
        now_version = ''
        if exists(exe_path):
            try:
                now_version = check_output(exe_path.replace('/','\\') + ' -version').decode('cp1251').strip()
            except BaseException:
                return None, None
        return now_version, True

    @classmethod
    def prepare_update(cls, new_ver):
        import urllib.request
        from bp_chat.logic.common.app_common import get_app_dir_path
        _p = get_app_dir_path()
        to_dir = join(_p, "loaded")
        if not exists(to_dir):
            makedirs(to_dir)
        if not exists(to_dir):
            return -13, None # Bad, but...

        updater_ver = Updater.load_updater_version()
        if not updater_ver:
            return -1, None
        to_updater_path = join(to_dir, "Uninstall.exe")
        _last_ver = None
        if exists(to_updater_path):
            _last_ver, ok = Updater.get_updater_version(to_updater_path)
            if not ok:
                return -11, 'Cant read version of updater' # Bad
        _new_upd_ver = _last_ver
        if _last_ver != updater_ver:
            if exists(to_updater_path):
                try:
                    os.remove(to_updater_path)
                except:
                    return -14, 'Cant remove last updater'
            if not Updater.download_updater(to_updater_path):
                return -2, None
            if not exists(to_updater_path):
                return -3, 'Updater downloaded but not found' # Bad
            _new_upd_ver, ok = Updater.get_updater_version(to_updater_path)
            if not ok:
                return -12, 'Updater downloaded but cant read version' # Bad
        if _new_upd_ver != updater_ver:
            return -4, None

        updater_exe_name = "Uninstall.exe"
        #if not exe_dir:
        updater_exe_dir = get_to_app_dir_path()
        updater_exe_path = join(updater_exe_dir, updater_exe_name)
        if exists(updater_exe_path):
            try:
                os.remove(updater_exe_path)
            except:
                return -15, "Cant remove updater local"
        try:
            shutil.copy2(to_updater_path, updater_exe_path)
        except:
            return -16, "Cant copy updater to local"

        _update_name = "bp_chat.update"
        if "-install_from_testing" in sys.argv:
            _update_name = "bp_chat.tst.update"
        to_path = join(to_dir, _update_name)
        url = "https://bp.compas.ru/pres/bp_chat/win/1_5/" + _update_name

        if exists(to_path):
            data = open(to_path, "rb").read()
            i = len(data)
            _min = i - 100
            _data = b''
            while True:
                i -= 1
                if i < _min:
                    _data = b''
                    break
                a = data[i:i+1]
                if a == b'|':
                    break
                _data = a + _data
            _data = _data.decode('utf-8')
            if _data == new_ver:
                #ChatApi.instance().callbacks.onNeedshowUpdateButtonSignal.emit()
                return 0, None

            try:
                os.remove(to_path)
            except:
                return -5, "Cant remove last update" # Bad

        try:
            urllib.request.urlretrieve(url, to_path)
        except BaseException:
            return -100, None

        if not exists(to_path):
            return -101, "Update downloaded but not found" # Bad

        #ChatApi.instance().callbacks.onNeedshowUpdateButtonSignal.emit()
        return 0, None

    @staticmethod
    def load_last_version(d=None, _default=None):
        if type(d) != dict:
            d = {'app': 'bp_chat', 'url':'chat-win-client'}
        try:
            _url = "https://bp.compas.ru/rapi/last_version/?app={}&base_ver=1_5".format(d['url'])
            if "-install_from_testing" in sys.argv:
                _url += "&type=testing"
            r = requests.get(_url, timeout=10)
        except BaseException as e:
            return _default
        return r.text

    def start_update(self):
        self._exec_command("update")

    # @staticmethod
    # def do_update():
    #     sleep(3)

    #     with open(Updater._update_path, "rb") as f:
    #         data = f.read()
    #     os.remove(Updater._update_path)
    #     imz = InMemoryZip()
    #     imz.write(data)
    #     updated_count = imz.unpack(imit=is_in_python())

    #     Updater._exec_command("")

    @staticmethod
    def _exec_command(com):
        if "debug" in sys.argv:
            com += " debug"

        com += " PID_" + str(os.getpid())

        if is_in_python():
            com = sys.executable + " main.py " + com
            Popen(com, shell=True)
        else:
            executable = sys.executable.lower().replace(".pyd",".py").replace(".py",".exe")
            com = executable + " " + com
            Popen(com, close_fds=True)


class InMemoryZip(object):

    to_package_folder = False
    extend_exes = False

    def __init__(self):
        self.in_memory_zip = StringIO()
        self.full_size = 0

    def write(self, data):
        self.in_memory_zip.write(data)

    def unpack(self, imit=False):
        self.in_memory_zip.seek(0)

        make_read_name = lambda name: name

        def write_file(name, data):
            dirr = dirname(abspath(name))
            if not exists(dirr):
                os.makedirs(dirr)
            with open(name, 'wb') as f:
                f.write(data)

        if imit:
            make_read_name = lambda name: name.replace('.pyd', '.py')
            write_file = lambda name, data: None

        count = 0

        with ZipFile(self.in_memory_zip) as myzip:
            for name in myzip.namelist():
                _lower_name = name.lower()
                if _lower_name in ('updater.pyd', "update.pyd", "main.pyd") or _lower_name.endswith(".exe") or (_lower_name.startswith("python") and _lower_name.endswith(".dll")):
                    continue
                read_name = make_read_name(name)
                last_data = None
                if exists(read_name):
                    last_data = open(read_name, 'rb').read()
                data = myzip.read(name)
                if data != last_data:
                    sz = len(data)
                    if name.startswith("ChatBoxWin/"):
                        name = name[len("ChatBoxWin/"):]
                    write_file(name, data)
                    count += 1

        return count