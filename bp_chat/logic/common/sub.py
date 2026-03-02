
import signal
import os, sys
from os.path import abspath, dirname, join
import psutil
from subprocess import Popen

from .processes import executable, is_in_python, exe_executable

PY_HERE = dirname(abspath(__file__))
PY_PROJ_PATH = dirname(dirname(dirname(PY_HERE)))


def start_sub(name=''):

    _is_python = is_in_python()
    if _is_python:
        com = sys.executable + " -m bp_chat " + name + " debug"
        cwd = PY_PROJ_PATH
    else:
        executable = exe_executable(with_path=True)
        com = executable + " " + name + " debug"
        cwd = os.path.dirname(executable)

    com = com.replace("\\","\\\\")

    com = com.split(" ")

    if _is_python:
        return Popen(com, shell=True, cwd=cwd)
    else:
        return Popen(com, close_fds=True, cwd=cwd)


def stop_sub(hidden=False):
    pid = find_my_sub(hidden=hidden)
    if pid != None:
        os.kill(int(pid), signal.SIGINT)
        return True


def find_my_sub(hidden=False):
    my_pid = os.getpid()

    _executable = executable().lower()
    _ex_name = os.path.basename(_executable)

    if not hidden:
        pass

    for proc in psutil.process_iter(attrs=['pid', 'name', 'username']):
        d = proc.info
        if d['pid'] == my_pid:
            continue
        if d['name'].lower() == _ex_name:
            p = psutil.Process(pid=d['pid'])
            cmd_lst = p.cmdline()
            cmd = ' '.join(cmd_lst).replace('\\\\', '\\').lower()
            if not hidden:
                pass
            p_exe = p.exe().lower()
            if (p_exe.startswith(_executable) or p_exe.endswith(_executable)): # name in cmd_lst and
                if not hidden:
                    pass
                return d['pid']