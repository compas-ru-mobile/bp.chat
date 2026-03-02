from PyQt5.QtWidgets import QWidget, QItemDelegate, QToolButton
from PyQt5.QtCore import Qt, QSize, QPointF
from PyQt5.QtGui import QColor, QIcon, QPainter

from .ui.UiServerSettingsWidget import Ui_ServerSettingsWidget

from ..logic.chat_api.ChatApi import ChatApi
from .core.draw import draw_badges, pixmap_from_file, change_widget_background_color


class ServerSettingsWidget(QWidget, Ui_ServerSettingsWidget):

    main_widget = None
    _sets = None

    def __init__(self, parent, main_widget, flags=Qt.Window, *args, **kwargs):
        super().__init__(parent)

        self.main_widget = main_widget

        self.setupUi(self)
        self.retranslateUi(self)

        self.initView()
        self.connectSignals()

    def initView(self):
        change_widget_background_color(self, QColor(255, 255, 255))
        change_widget_background_color(self.topWidget, QColor(255, 193, 7))
        self.organizerWidget.hide()

    def connectSignals(self):
        self.organizerCheckBox.stateChanged.connect(self.organizerCheckBoxStateChanged)
        self.saveButton.clicked.connect(self.saveButtonClicked)

    def gotServerSettings(self, d):
        self._sets = d
        self.organizerCheckBox.setChecked(d.get('organizer', False))
        self.parse_dict(d)

    def parse_dict(self, d, prefix=''):
        for name, value in d.items():
            if len(prefix) > 0:
                if not name.startswith(prefix):
                    name = prefix + '_' + name.lower()
            if type(value) == dict:
                self.parse_dict(value, name)
            else:
                w = getattr(self, name, None)
                if w and value != None:
                    w.setText(str(value))

    def organizerCheckBoxStateChanged(self, state):
        self.organizerWidget.setVisible(self.organizerCheckBox.isChecked())

    def saveButtonClicked(self):
        self.parse_dict_for_save(self._sets)
        ChatApi.instance().set_server_settings(self._sets)

    def parse_dict_for_save(self, d, prefix=''):
        for name, value in d.items():
            _name = name
            if len(prefix) > 0:
                if not name.startswith(prefix):
                    name = prefix + '_' + name.lower()
            if type(value) == dict:
                self.parse_dict_for_save(value, name)
            else:
                w = getattr(self, name, None)
                if w:
                    if w.text() != value:
                        d[_name] = w.text()


