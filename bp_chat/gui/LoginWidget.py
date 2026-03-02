from PyQt5.QtWidgets import QWidget, QItemDelegate, QToolButton, QPushButton
from PyQt5.QtCore import Qt, QSize, QPointF, QEvent
from PyQt5.QtGui import QColor, QIcon, QPainter

from .ui.UiLoginWidget import Ui_LoginWidget

from ..logic.chat_api.ChatApi import ChatApi
from .core.draw import draw_badges, pixmap_from_file, change_widget_background_color
from .views.UpdateButtonDraw import UpdateButtonDraw
from bp_chat.gui.common.langs import tr_w


class LoginWidget(QWidget, Ui_LoginWidget):

    main_widget = None

    def __init__(self, parent, main_widget, flags=Qt.Window, *args, **kwargs):
        super().__init__(parent)

        self.main_widget = main_widget

        self.setupUi(self)
        self.retranslateUi(self)

        self.initView()
        self.connectSignals()

    def initView(self):
        self.faviconLabel.setPixmap(pixmap_from_file("favicon", 50, 50))
        self.showError(None)
        change_widget_background_color(self, QColor(255, 193, 7))
        self.nameLineEdit.setFocus()

        if not self.main_widget.server_setting_visible:
            self.serverButton.hide()
        if self.main_widget.other_login_widget_title:
            self.label.setText(self.main_widget.other_login_widget_title)
        if self.main_widget.on_init_login_widget:
            self.main_widget.on_init_login_widget(self)

        self.onRegisterStateChanged()

        self.makeUpdateButton()

    def connectSignals(self):
        tr_w(self.loginButton).clicked.connect(self.onLoginClick)
        tr_w(self.signinButton).clicked.connect(self.onSigninClick)
        tr_w(self.serverButton).clicked.connect(self.onServerClick)
        self.passwordLineEdit.installEventFilter(self)
        self.nameLineEdit.installEventFilter(self)
        self.confirmPasswordLineEdit.installEventFilter(self)
        tr_w(self.registerCheckBox).stateChanged.connect(self.onRegisterStateChanged)
        tr_w(self.updateButton).clicked.connect(self.main_widget.onUpdateButtonClicked)

    def makeUpdateButton(self):
        self.updateButton = QPushButton(self)
        self.updateButton.setFlat(True)
        self.updateButton.setText("Update")
        self.updateButton.hide()
        UpdateButtonDraw(self.updateButton)

    def showUpdateButton(self):
        self.updateButton.show()
        self.updateUpdateButtonPos()

    def updateUpdateButtonPos(self):
        self.updateButton.move(5, self.height() - self.updateButton.height() - 5)

    def resizeEvent(self, e):
        self.updateUpdateButtonPos()
        return super().resizeEvent(e)

    def eventFilter(self, object, event):

        if event.type() == QEvent.KeyPress:

            is_key_enter = (event.key() == Qt.Key_Enter) or (event.key() == Qt.Key_Return)
            if object == self.passwordLineEdit or object == self.confirmPasswordLineEdit:
                if event.type() == QEvent.KeyPress:
                    #is_enter = event.key() & Qt.Key_Enter == event.key()
                    #is_enter_with_ctrl = is_enter and event.modifiers() == Qt.ControlModifier
                    if is_key_enter:
                        self.onLoginClick()
                        return True
            elif object == self.nameLineEdit:
                if event.type() == QEvent.KeyPress:
                    #is_enter = event.key() & Qt.Key_Enter == event.key()
                    #is_enter_with_ctrl = is_enter and event.modifiers() == Qt.ControlModifier
                    if is_key_enter:
                        self.passwordLineEdit.setFocus()
                        return True

        return super().eventFilter(object, event)

    def showError(self, error, clear=True):
        if error == None:
            self.infoLabel.hide()
            self.errorLabel.hide()
            self.signinButton.show()
            self.loginButton.hide()
            self.registerCheckBox.hide()
            self.loginLayoutWidget.hide()
        else:
            self.errorLabel.setText(error)
            self.infoLabel.hide()
            self.errorLabel.show()
            self.signinButton.hide()
            self.loginButton.show()
            self.registerCheckBox.show()
            self.loginLayoutWidget.show()
            if clear:
                self.nameLineEdit.setText("")
                self.passwordLineEdit.setText("")
                self.confirmPasswordLineEdit.setText("")
            self.nameLineEdit.setFocus()

        self.onRegisterStateChanged()

    def onLoginClick(self):

        name = self.nameLineEdit.text().strip()
        pwd = self.passwordLineEdit.text().strip()
        confirm = self.confirmPasswordLineEdit.text().strip()

        is_register = self.registerCheckBox.isChecked()
        if len(name) == 0:
            self.showError("Please input name", clear=False)
            return
        if len(name) < 2:
            self.showError("Too short name", clear=False)
            return
        if len(pwd) == 0:
            self.showError("Please input password", clear=False)
            return
        if len(pwd) < 4:
            self.showError("Too short password", clear=False)
            return
        if is_register:
            if confirm != pwd:
                self.showError("Passwords do not match", clear=False)
                return

        chatApi = ChatApi.instance()

        self.main_widget.clearChatsList()
        self.main_widget.showChatsList(withTitle=True)
        self.main_widget.showError("Auth started...")

        chatApi.connect(
            name=name,
            pwd=pwd,
            register=is_register
        )

    def onSigninClick(self):
        chatApi = ChatApi.instance()

        self.main_widget.clearChatsList()
        self.main_widget.showChatsList(withTitle=True)
        self.main_widget.showError("Auth started...")

        chatApi.connect()

    def onServerClick(self):
        self.main_widget.showServer()

    def onRegisterStateChanged(self):
        signin_visible = self.signinButton.isVisible()

        # if changeRegisterVisible:
        #     self.registerCheckBox.setVisible(not signin_visible)

        visible = self.registerCheckBox.isChecked() and not signin_visible
        self.confirmPasswordLabel.setVisible(visible)
        self.confirmPasswordLineEdit.setVisible(visible)
        title, button_text = ("Sign up", "Register") if visible else ("Sign in", "Login")
        self.label.setText(title)
        self.loginButton.setText(button_text)