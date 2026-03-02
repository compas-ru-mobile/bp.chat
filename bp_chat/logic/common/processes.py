
import sys, os


def is_in_python():
    app_is_python = False
    _here = os.path.abspath(__file__)
    if sys.executable:
        executable = sys.executable.replace("\\", "/").split("/")[-1].lower().split(".")[0]
        if executable.startswith("python"):
            app_is_python = True
    if not os.path.exists(_here) or 'IMIT_EXE' in sys.argv:
        app_is_python = False
    return app_is_python


def executable(with_path=False):
    if is_in_python():
        return sys.executable.lower()
    return exe_executable(with_path)


def exe_executable(with_path=False):
    if with_path:
        return sys.argv[0]
    return 'bp_chat.exe'