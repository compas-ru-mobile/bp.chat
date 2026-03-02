from PyQt5.QtWidgets import QSystemTrayIcon, QAction, QMenu
from PyQt5.QtGui import QIcon
from sys import platform
from bp_chat.gui.core.animate import SystemTrayIcon as _SystemTrayIcon
from bp_chat.gui.common.langs import tr

if platform.startswith('win'):
    from bp_chat.update import is_installed, do_install, do_uninstall
else:
    is_installed = lambda: None
    do_install = lambda *args,**kwargs: None
    do_uninstall = lambda *args, **kwargs: None


def make_tray_icon(app, parent, main_icon):
    icon = SystemTrayIcon(main_icon, parent)
    icon.app = app

    def _on_close(*args):
        icon.hide()

    app.lastWindowClosed.connect(_on_close)

    icon.show()
    return icon


class SystemTrayIcon(_SystemTrayIcon):

    app = None
    parent_widget = None

    def __init__(self, icon, parent=None):
        _SystemTrayIcon.__init__(self, icon, parent, None)

        self.autostartAction = QAction('', self)
        self.autostartAction.to_auto_start = True
        self.autostartAction.triggered.connect(self.to_autostart)
        self.menu.addAction(self.autostartAction)

        if is_installed():
            self.autostartAction.to_auto_start = False
        self.to_autostart_update()

    def to_autostart(self):
        if self.autostartAction.to_auto_start:
            do_install(None, only_auto_start=True)
        else:
            do_uninstall(None, only_auto_start=True)
        self.autostartAction.to_auto_start = not self.autostartAction.to_auto_start
        self.to_autostart_update()

    def to_autostart_update(self):
        if self.autostartAction.to_auto_start:
            self.autostartAction.setText(tr('Add to Autostart'))
        else:
            self.autostartAction.setText(tr('Remove from Autostart'))
