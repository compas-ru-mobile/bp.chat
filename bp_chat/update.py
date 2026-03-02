try:
    from win32com.client import Dispatch
except BaseException:
    print('ERROR: cant import Dispatch')
import os, shutil


# def do_update(tunes):
#     from bp_chat.logic.file_load.Updater import Updater
#     Updater.do_update()

def is_installed():
    from bp_chat.logic.common.app_common import APP_TITLE, APP_NAME_DIR, get_to_app_dir_path
    APPDATA = os.getenv('APPDATA')
    autostart_lnk_dir = APPDATA + '/Microsoft/Windows/Start Menu/Programs/Startup'
    autostart_lnk_path = autostart_lnk_dir + "/" + APP_TITLE + ".lnk"
    installed = os.path.exists(autostart_lnk_path)
    return installed

def do_install(tunes, only_auto_start=False):
    from bp_chat.logic.common.app_common import APP_TITLE, APP_NAME_DIR, get_to_app_dir_path
    desktop_path = os.path.expanduser("~/Desktop")
    dir_path = get_to_app_dir_path()
    to_exe_path = dir_path + "/" + APP_NAME_DIR + ".exe"
    APPDATA = os.getenv('APPDATA')

    if not only_auto_start:
        createShortcut(
            path = desktop_path + "/" + APP_TITLE + ".lnk",
            target = to_exe_path,
            wDir = dir_path
        )

        start_menu_path = APPDATA + '/Microsoft/Windows/Start Menu/' + APP_TITLE
        start_lnk_path = start_menu_path + "/" + APP_TITLE + ".lnk"
        if not os.path.exists(start_menu_path):
            os.makedirs(start_menu_path)

        createShortcut(
            path = start_lnk_path,
            target = to_exe_path,
            wDir = dir_path
        )

    autostart_lnk_dir = APPDATA + '/Microsoft/Windows/Start Menu/Programs/Startup'
    autostart_lnk_path = autostart_lnk_dir + "/" + APP_TITLE + ".lnk"
    createShortcut(
        path=autostart_lnk_path,
        target=to_exe_path,
        wDir=autostart_lnk_dir
    )

def do_uninstall(tunes, only_auto_start=False):
    from bp_chat.logic.common.app_common import APP_TITLE
    desktop_path = os.path.expanduser("~/Desktop")
    APPDATA = os.getenv('APPDATA')

    path = desktop_path + "/" + APP_TITLE + ".lnk"
    if not only_auto_start:
        if os.path.exists(path):
            os.remove(path)

        start_menu_path = APPDATA + '/Microsoft/Windows/Start Menu/' + APP_TITLE
        if os.path.exists(start_menu_path):
            shutil.rmtree(start_menu_path)

    autostart_lnk_dir = APPDATA + '/Microsoft/Windows/Start Menu/Programs/Startup'
    autostart_lnk_path = autostart_lnk_dir + "/" + APP_TITLE + ".lnk"
    os.remove(autostart_lnk_path)


def createShortcut(path, target='', wDir='', icon=''):
    # ext = path[-3:]
    # if ext == 'url':
    #     shortcut = file(path, 'w')
    #     shortcut.write('[InternetShortcut]\n')
    #     shortcut.write('URL=%s' % target)
    #     shortcut.close()
    if True:
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wDir
        if icon == '':
            pass
        else:
            shortcut.IconLocation = icon
        shortcut.save()
