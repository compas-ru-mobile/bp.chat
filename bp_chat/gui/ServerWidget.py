from PyQt5.QtWidgets import QWidget, QItemDelegate, QToolButton
from PyQt5.QtCore import Qt, QSize, QPointF, QEvent, pyqtSignal
from PyQt5.QtGui import QColor, QIcon, QPainter

from .ui.UiServerWidget import Ui_ServerWidget

from ..logic.chat_api.ChatApi import ChatApi
from .core.draw import draw_badges, pixmap_from_file, change_widget_background_color
from bp_chat.gui.common.langs import tr_w


class ServerWidget(QWidget, Ui_ServerWidget):

    showErrorSignal = pyqtSignal(object)

    main_widget = None

    def __init__(self, parent, main_widget, flags=Qt.Window, *args, **kwargs):
        super().__init__(parent)

        self.main_widget = main_widget

        self.setupUi(self)
        self.retranslateUi(self)

        self.initView()
        self.connectSignals()

    def initView(self):
        tr_w(self.serverLabel)
        tr_w(self.server2CheckBox)
        tr_w(self.infoLabel)
        tr_w(self.infoLabel_2)
        tr_w(self.saveButton)

        self.faviconLabel.setPixmap(pixmap_from_file("favicon", 50, 50))
        change_widget_background_color(self, QColor(255, 193, 7))
        self.showError(None)
        self.updateValuesFromChatApi()

    def updateValuesFromChatApi(self):
        chatApi = ChatApi.instance()
        self.serverLineEdit.setText(chatApi.serverAddress)
        self.server2CheckBox.setChecked(chatApi.useServer2)
        self.server2LineEdit.setText(chatApi.serverAddress2)

    def connectSignals(self):
        self.saveButton.clicked.connect(self.onSaveClick)
        self.serverLineEdit.installEventFilter(self)
        self.server2LineEdit.installEventFilter(self)
        self.showErrorSignal.connect(self.showErrorSlot)

    def onSaveClick(self):
        chatApi = ChatApi.instance()
        chatApi.serverAddress = self.serverLineEdit.text()
        chatApi.serverAddress2 = self.server2LineEdit.text()
        chatApi.useServer2 = self.server2CheckBox.isChecked()
        self.main_widget.showLogin()

    def showError(self, error_text):
        self.showErrorSignal.emit(error_text)

    def showErrorSlot(self, errorText):

        if errorText == None:
            self.errorLabel.hide()
            return

        self.errorLabel.setText(errorText)
        self.errorLabel.show()

    def eventFilter(self, object, event):
        if object == self.serverLineEdit or object == self.server2LineEdit:
            if event.type() == QEvent.KeyPress:
                is_enter = event.key() & Qt.Key_Enter == event.key()
                is_enter_with_ctrl = is_enter and event.modifiers() == Qt.ControlModifier
                if is_enter:
                    self.onSaveClick()
                    return True
        return super().eventFilter(object, event)