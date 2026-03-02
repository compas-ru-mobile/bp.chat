import sys
from PyQt5.QtWidgets import QWidget, QItemDelegate, QToolButton
from PyQt5.QtCore import Qt, QSize, QPointF
from PyQt5.QtGui import QColor, QIcon, QPainter

from .ui.UiSettingsWidget import Ui_SettingsWidget

from .core.draw import draw_badges, pixmap_from_file, change_widget_background_color, pixmap_from_icon, pixmap_from_icon_rounded, icon_from_file

from .ChatEditDialog import ChatEditDialog
from ..logic.chat_api.ChatApi import ChatApi
from .common.langs import tr, tr_w, change_lang


class SettingsWidget(QWidget, Ui_SettingsWidget):

    main_widget = None

    def __init__(self, parent, main_widget, flags=Qt.Window, *args, **kwargs):
        super().__init__(parent)

        self.main_widget = main_widget

        self.setupUi(self)
        self.retranslateUi(self)

        self.initView()
        self.connectSignals()

        if self.main_widget.on_init_settings_widget:
            self.main_widget.on_init_settings_widget(self)

    def initView(self):
        change_widget_background_color(self, QColor(255, 255, 255))
        change_widget_background_color(self.userLayoutWidget, QColor(255, 193, 7))
        change_widget_background_color(self.toolBarWidget, QColor(255, 193, 7))

        self.userAvatarLabel.setPixmap(pixmap_from_file("favicon", 50, 50))

        tr_w(self.label)
        tr_w(self.logoutButton).setIcon(icon_from_file("logout"))
        tr_w(self.disconnectButton).setIcon(icon_from_file("disconnect"))
        self.backButton.setIcon(icon_from_file("arrow_back"))
        tr_w(self.createChatButton).setIcon(icon_from_file("create_group"))

        conf = ChatApi.instance().conf
        userFontSize = conf.window_fontSize

        if userFontSize == 1:
            self.fontSizeRB.setChecked(True)
            userFontSize = 1
        elif userFontSize == 2:
            self.fontSizeRB_2.setChecked(True)
        elif userFontSize == 3:
            self.fontSizeRB_3.setChecked(True)

        if "preview" not in sys.argv:
            self.fontSizeBox.setVisible(False)

    def updateNavigationDrawer(self):
        chatApi = ChatApi.instance()
        userProfile = chatApi.userProfile
        bitmap = None
        fullname = "Unknown"

        if userProfile != None:
            fullname = userProfile.getFullNameWithId()
            bitmap = userProfile.getBitmap()

        self.userNameLabel.setText(fullname)

        if bitmap == None:
            self.userAvatarLabel.setPixmap(pixmap_from_file("favicon", 100, 100))
        else:
            #self.userAvatarLabel.setPixmap(pixmap_from_icon(bitmap, 100, 100))
            pixmap = pixmap_from_icon_rounded(bitmap, to_size=(100, 100), border_radius=10)
            if pixmap:
                self.userAvatarLabel.setPixmap(pixmap)

        if chatApi.isUserGuest():
            self.createChatButton.hide()
        else:
            self.createChatButton.show()

        if chatApi.is_admin:
            self.serverSettingsButton.show()
            self.upgradeToProButton.show()
        else:
            self.serverSettingsButton.hide()
            self.upgradeToProButton.hide()

    def connectSignals(self):
        self.backButton.clicked.connect(self.onBackClick)
        self.logoutButton.clicked.connect(self.onLogoutClick)
        self.disconnectButton.clicked.connect(self.onDisconnectClick)
        self.createChatButton.clicked.connect(self.onCreateNewGroupClicked)
        self.serverSettingsButton.clicked.connect(self.serverSettingsButtonClicked)
        self.upgradeToProButton.clicked.connect(self.upgradeToProButtonClicked)
        self.langButton.clicked.connect(self.onLangClick)
        # self.fontSizeBox.clicked.connect(self.onFontSizeClick)
        self.fontSizeRB.clicked.connect(self.onFontSizeClick)
        self.fontSizeRB_2.clicked.connect(self.onFontSizeClick)
        self.fontSizeRB_3.clicked.connect(self.onFontSizeClick)

    def setAppVersion(self, version):
        self.versionLabel.setText(str(version))

    def onBackClick(self):
        self.main_widget.showChatsList(withTitle=True)

    def onLogoutClick(self):
        self.main_widget.showLogin()
        ChatApi.instance().logout()
        self.main_widget.closeOpenedChat()

    def onDisconnectClick(self):
        self.main_widget.showLogin()
        ChatApi.instance().disconnect()
        self.main_widget.closeOpenedChat()

    def onCreateNewGroupClicked(self):
        self.onBackClick()
        dialog = ChatEditDialog(self.main_widget)
        dialog.exec()

    def serverSettingsButtonClicked(self):
        self.main_widget.showServerSettings()

    def upgradeToProButtonClicked(self):
        from webbrowser import open_new_tab
        open_new_tab("https://bp.compas.ru/chat2/upgrade_info")

    def onLangClick(self):
        change_lang()

    def onFontSizeClick(self):
        userFontSize = 0
        if self.fontSizeRB.isChecked():
            userFontSize = 1
        elif self.fontSizeRB_2.isChecked():
            userFontSize = 2
        elif self.fontSizeRB_3.isChecked():
            userFontSize = 3

        conf = ChatApi.instance().conf
        conf.window_fontSize = userFontSize

        self.main_widget.changeFontSize(userFontSize)



