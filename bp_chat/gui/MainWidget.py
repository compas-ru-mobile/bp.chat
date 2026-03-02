
from genericpath import exists
from ntpath import join
from os import makedirs
from os.path import basename, getsize
import sys

from PyQt5.QtWidgets import (QWidget, QAbstractItemView, QHBoxLayout, QFileDialog, QMessageBox, QApplication,
                             QSystemTrayIcon, QMenu)
from PyQt5.QtCore import Qt, QSize, QEvent, QObject, pyqtSignal, QPoint
from PyQt5.QtGui import QColor, QIcon, QKeySequence, QKeyEvent, QFontMetrics, QPalette

from bp_chat.logic.chat_api.ChatApiCommon import by_timer
from bp_chat.logic.file_load.Updater import Updater
from .common.tray_icon import make_tray_icon
from .common.draw_funcs import makeResendWidgetBase
from .ui.UiMainWidget import Ui_MainWidget
from ..logic.chat_api.ChatApi import ChatApi, ChatApiCallbacks
from .delegates.ChatsListDelegate import ChatsListModel

from .InputCallWidget import InputCallWidget

from bp_chat.logic.common.app_common import APP_TITLE
from .models.model_items import MessageItem
from ..core.app import App
from ..gui.core.singles import MessagesForSend
from ..gui.core.draw import set_DRAW_ICON_FROM_QRC, icon_from_file
from .models.list_model import set_NEED_DRAW_PPARTS
from .models.funcs import FULL_STYLESHEET
from .common.langs import tr, tr_w

from .delegates.MessagesDictDelegate import MessagesDictModel, MessagesDictDelegate
from ..logic.datas.User import User
from ..logic.datas.UserChat import UserChat
from ..logic.datas.GroupChat import GroupChat
from ..logic.datas.Message import Message
from .core.draw import change_widget_background_color, draw_badges_on_icon, pixmap_from_file, pixmap_from_icon_rounded
from .common.system_info import get_download_path
from .LoginWidget import LoginWidget
from .SettingsWidget import SettingsWidget
from .ProfileWidget import ProfileWidget
from .SelectChatWidget import SelectChatWidget
from .ChatEditDialog import ChatEditDialog
from .FileDialog import FileDialog
from .ServerWidget import ServerWidget
from .ServerSettingsWidget import ServerSettingsWidget
from .views.ChatsListView import ChatsListView
from .views.MessagesListView import MessagesListView
from .views.FilterButtonControl import FilterButtonsControl
from .views.RightStackDraw import RightWidgetDraw
from .views.UpdateButtonDraw import UpdateButtonDraw
from ..gui.views.CssClassControl import cssClassControl
from bp_chat.core.tryable import ConsoleThread


import traceback
colored = lambda text, color: text


from ..logic.chat_api.ChatApiCommon import ALPHAVET_SIMPLE, SMILES, tryable, SMILES_DICT


class Callbacks(QObject, ChatApiCallbacks):

    connectedCallbackSignal = pyqtSignal()
    disconnectedCallbackSignal = pyqtSignal()
    gotLoggedInCallbackSignal = pyqtSignal()
    gotConnectFinCallbackSignal = pyqtSignal()
    gotUsersListCallbackSignal = pyqtSignal(object)
    gotChatsListCallbackSignal = pyqtSignal(object)
    chatOpenedCallbackSignal = pyqtSignal(object, object)
    messagesUpdateCallbackSignal = pyqtSignal(object)
    needRegisterCallbackSignal = pyqtSignal()
    needShowErrorCallbackSignal = pyqtSignal(object, object)
    chatsUpdatedListCallbackSignal = pyqtSignal()
    updateNavigationDrawerCallbackSignal = pyqtSignal()
    gotAvatarCallbackSignal = pyqtSignal()
    updateUserProfileCallbackSignal = pyqtSignal(object)
    changeUserTypeCallbackSignal = pyqtSignal(object)
    gotChatUsersCallbackSignal = pyqtSignal(object)
    fileProgressCallbackSignal = pyqtSignal(object, object, object)
    closeResendWidgetSignal = pyqtSignal()
    needShowNotifySignal = pyqtSignal(object, object)
    needShowSmartInfoSignal = pyqtSignal(object)
    needApplyBadgesSignal = pyqtSignal(object)
    lastVersionGreaterSignal = pyqtSignal(object)
    onNeedshowUpdateButtonSignal = pyqtSignal()
    onNewUpdateProgressSignal = pyqtSignal(object)
    gotServerSettingsSignal = pyqtSignal(object)
    gotServerInfoSignal = pyqtSignal(object)
    needCloseAllOpenedWindowsSignal = pyqtSignal()
    onAdmInfoSignal = pyqtSignal(object)
    needRaiseWindowSignal = pyqtSignal()
    needShowChatSignal = pyqtSignal(object, object)
    onInputCallSignal = pyqtSignal(object)
    needShowFindLineSignal = pyqtSignal(object)

    def __init__(self, parent):
        self.mw: MainWidget = parent
        super().__init__(parent)
        ChatApiCallbacks.__init__(self)

        for name in ChatApiCallbacks._abs_methods:
            sig = getattr(self, name + "Signal", None)
            slot = getattr(self, name)
            if sig:
                self._make_sigstarter(name, sig, slot)
                sig.connect(slot)

    @tryable
    def connectedCallback(self):
        self.mw.showChatsList(withTitle=True)
        self.mw.setToolbarSubtitle(tr("Loading")+"...")

    @tryable
    def disconnectedCallback(self):
        self.mw.showLogin(None)

    @tryable
    def gotLoggedInCallback(self):
        pass

    @tryable
    def gotUsersListCallback(self, users):
        pass

    @tryable
    def gotChatsListCallback(self, chats):
        self.mw.updateChatsListView(source='gotChatsListCallback')

    @tryable
    def gotConnectFinCallback(self):
        self.mw.setToolbarSubtitle(None)
        if (self.mw.updateGuestMode(None, "gotConnectFinCallback")):
            return

        if self.mw._open_chat_id != None:
            open_chat_id = self.mw._open_chat_id
            self.mw.set_open_chat_id(None)
            self.mw.showChat(open_chat_id, None)
            ChatApi.instance().openChat(open_chat_id)

    @tryable
    def chatOpenedCallback(self, openedChatId, withOpenChat):
        chatName = None
        chat = ChatApi.instance().getChatById(openedChatId)
        if chat != None:
            chatName = chat.getName()

        self.mw.chatListView.set_opened(1)

        if withOpenChat:
            self.mw.showChat(openedChatId, chatName)
        else:
            self.mw.setToolbarTitle(ChatApi.instance().getAppName())

        self.mw.setToolbarSubtitle(None)

    @tryable
    def messagesUpdateCallback(self, withScrollToBottom):
        _err = None
        if withScrollToBottom == None:
            _err = False
        self.mw.showError(_err)
        self.mw.updateMessages(withScrollToBottom)

    @tryable
    def needRegisterCallback(self):
        self.mw.showLogin(tr("Please sign in"))

    @tryable
    def needShowErrorCallback(self, error, message):
        if error == ChatApi.ERROR_NOSERVERS or error == ChatApi.ERROR_WRONG_SERVER_1 or error == ChatApi.ERROR_WRONG_SERVER_2:

            ChatApi.instance().stopConnecting()
            self.mw.showServer(message)

        elif error == ChatApi.ERROR_NO_AUTH_DEACTIVATED or error == ChatApi.ERROR_LOGIN_OCCUPIED:

            ChatApi.instance().stopConnecting()
            self.mw.showLogin(message)

        elif error == ChatApi.ERROR_API_CLIENT_OLD:

            self.mw.showServer(message)

        elif error == ChatApi.ERROR_API_SERVER_OLD:

            self.mw.showServer(message)

        elif error == ChatApi.ERROR_NO_CONNECT:

            self.mw.onNoConnect()

        self.mw.showError(message)

    @tryable
    def chatsUpdatedListCallback(self):
        if self.mw.updateGuestMode(None, "chatsUpdatedListCallback"):
            pass
        else:
            self.mw.updateChats()
        self.mw.updateOpenedChat()
        self.mw.updateBadges()

    @tryable
    def updateNavigationDrawerCallback(self):
        self.mw.updateNavigationDrawer()

    @tryable
    def gotAvatarCallback(self):
        self.mw.updateAvatars()

    @tryable
    def updateUserProfileCallback(self, user_id):
        self.mw.updateProfile(ChatApi.instance().getUser(user_id).profile)
        self.mw.updateChatsListView(source='updateUserProfileCallback')

    @tryable
    def changeUserTypeCallback(self, user_type):
        self.mw.updateGuestMode(user_type, "changeUserTypeCallback")

    @tryable
    def gotChatUsersCallback(self, users):
        cef = self.mw.tryCurrentChatEdit()
        if cef != None:
            cef.setCheckedUsers(users)

    @tryable
    def fileProgressCallback(self, fileId, progress, download):
        self.mw.onFileProgress(fileId, progress, download)

    @tryable
    def closeResendWidget(self):
        self.mw.closeResendWidget()

    @tryable
    def needShowNotify(self, noti_text, title):
        self.mw.show_notify(noti_text, second_title=title)

    @tryable
    def needShowSmartInfo(self, smart_text):
        self.mw.show_smart_info(smart_text)

    @tryable
    def needApplyBadges(self, badgesCount):
        self.mw.applyBadges(badgesCount)

    @tryable
    def lastVersionGreater(self, ver):
        self.mw.loadUpdatePack(ver)

    @tryable
    def onNeedshowUpdateButton(self):
        self.mw.showUpdateButton()

    @tryable
    def onNewUpdateProgress(self, progress):
        self.mw.setUpdateProgress(progress)

    @tryable
    def onNeedCloseApp(self):
        self.mw.closeNow()

    @tryable
    def gotServerSettings(self, d):
        self.mw.gotServerSettings(d)

    @tryable
    def gotServerInfo(self, d):
        self.mw.updateServerInfo(d)

    @tryable
    def needCloseAllOpenedWindows(self):
        self.mw.closeAllOpenedWindows()

    @tryable
    def onAdmInfo(self, d):
        self.mw.onAdmInfo(d)

    @tryable
    def needRaiseWindow(self):
        self.mw.showNormal()
        self.mw.activateWindow()

    @tryable
    def needShowChat(self, chat_id, chat_name):
        if chat_id < 0:
            self.mw.showChat(chat_id, chat_name)
        else:
            self.mw.showChatWithOpen(chat_id)

    @tryable
    def onInputCall(self, text):
        self.mw.showInputCall(text)

    @tryable
    def needShowFindLine(self, val):
        self.mw.showFindLine(val)

    def _make_sigstarter(self, name, sig, slot):
        def _func(*args, **kwargs):
            return sig.emit(*args, **kwargs)
        setattr(self, name + "Slot", slot)
        setattr(self, name, _func)


class MainWidget(QWidget, Ui_MainWidget):

    settingsWidget = None
    chatEditDialog = None
    profileWidget = None
    loginWidget = None

    tunes = None
    clipboard = None
    has_ctrl = False
    was_maximized = False
    _open_chat_id = None
    _current_chat_name = ''

    copyEvent = pyqtSignal()

    # For admin:
    server_setting_visible = True
    other_login_widget_title = None
    on_no_connect_callback = None
    on_want_close_callback = None
    on_init_settings_widget = None
    on_init_login_widget = None

    input_call_widget = None
    tray_icon = None

    def __init__(self, app=None, flags = Qt.Window, *args, **kwargs): #| Qt.FramelessWindowHint
        super().__init__(parent=None, flags=flags)
        self.app = app
        App.instance().main_widget = self

        if 'PPARTS' in sys.argv:
            set_NEED_DRAW_PPARTS(True)

        set_DRAW_ICON_FROM_QRC(True)

        self.setupUi(self)
        self.retranslateUi(self)

        if 'input_call' in sys.argv:
            self.showInputCall('888')

        self.pages = {
            "login": {"cls": LoginWidget, "object": None, "page": 1, "stacked": self.stackedWidget},
            "server": {"cls": ServerWidget, "object": None, "page": 2, "stacked": self.stackedWidget},
            "settings": {"cls": SettingsWidget, "object": None, "page": 1, "stacked": self.leftStackedWidget},
            "profile": {"cls": ProfileWidget, "object": None, "page": 1, "stacked": self.rightStackedWidget},
            "selectChat": {"cls": SelectChatWidget, "object": None, "page": 2, "stacked": self.rightStackedWidget},
            'serverSettings': {"cls": ServerSettingsWidget, "object": None, "page": 3, "stacked": self.rightStackedWidget},
        }

        self.initListView()
        self.initKwargs(kwargs)
        self.connectSignals()
        self.initStart()

    def initKwargs(self, kwargs):
        self.server_setting_visible = kwargs.get('server_setting_visible', True)
        other_window_title = kwargs.get('other_window_title', None)
        if other_window_title:
            self.setWindowTitle(other_window_title)
        self.other_login_widget_title = kwargs.get('other_login_widget_title', None)
        self.on_no_connect_callback = kwargs.get('on_no_connect_callback', None)
        self.on_want_close_callback = kwargs.get('on_want_close_callback', None)
        self.on_init_settings_widget = kwargs.get('on_init_settings_widget', None)
        self.on_init_login_widget = kwargs.get('on_init_login_widget', None)

    def initListView(self):
        ChatApi.instance().connect_callbacks(Callbacks(self))

        chatsListPageLayout = self.chatsListPage.layout()
        chatLayout = self.chatListViewLayout
        self.listView.hide()
        self.chatListView.hide()

        self.smartTextLabel = RightWidgetDraw(self.rightWidget)
        self.smartTextLabel.hide()

        from .core.draw import icon_from_file

        main_icon = icon_from_file("favicon")
        self.setWindowIcon(main_icon)

        self.tray_icon = make_tray_icon(self.app, self, main_icon)

        self.textEdit.setAcceptRichText(False)

        newListView = ChatsListView(self)
        self.filterControl = FilterButtonsControl(
            allButton=self.allButton,
            groupsButton=self.groupsButton,
            contactsButton=self.contactsButton,
            liveButton=self.liveButton,
            main_widget=self
        )
        newListView.setFont(self.listView.font())
        newListView.setFrameShape(self.listView.frameShape())
        newListView.setVerticalScrollMode(self.listView.verticalScrollMode())
        newListView.setHorizontalScrollMode(self.listView.horizontalScrollMode())
        chatsListPageLayout.replaceWidget(self.listView, newListView)
        self.listView = newListView

        def on_chat_selected(selected_chats):
            self.closeResendWidget()
            if selected_chats:
                chat = selected_chats[0].chat
                ChatApi.instance().on_chat_selected(chat)
            #     chat = selected_chats[0].chat
            #     # // FIXME create private group
            #     chat_id = chat.id
            #     if chat_id < 0:
            #         chat_api = ChatApi.instance()
            #         if chat != None and chat.is_private() and chat_api.creatingChat == None:
            #             # FIXME : hack...
            #             chat_api.creatingChat = chat
            #             userChat = chat
            #             he_id = userChat.user.id
            #             chat_api.send(url="/group/", attrs={
            #                 "method": "POST",
            #                 "group_name": "private-" + str(chat_api.getCurrentUserId()) + "," + str(he_id),
            #                 "group_type": "private",
            #                 "users": str(chat_api.getCurrentUserId()) + "," + str(he_id)
            #             })
            #             self.showChat(chat_id, chat.getName())
            #     else:
            #         self.showChatWithOpen(chat_id)

        newListView.set_selected_callback(on_chat_selected)

        self.mesesForSend = MessagesForSend()

        # FIXME
        newListView = MessagesListView(self.verticalChatWidget) #, self)
        newListView.setFont(self.chatListView.font())
        newListView.setFrameShape(self.chatListView.frameShape())
        newListView.setVerticalScrollMode(self.chatListView.verticalScrollMode())
        newListView.setHorizontalScrollMode(self.chatListView.horizontalScrollMode())
        newListView.setSelectionMode(QAbstractItemView.NoSelection)
        chatLayout.replaceWidget(self.chatListView, newListView)
        self.chatListView = newListView

        self.chatTitleLabel.installEventFilter(self)

        self.updateChatsListView(start=True, source='initListView')

        # FIXME small hack for line...
        self.sendLayoutWidget.setStyleSheet(
            "background-color: white; "
            "border-width: 1px; "
            "border-top-style: solid; border-right-style: none; border-bottom-style: none; border-left-style: none; "
            "border-color: #cccccc; ") # rgb(255, 193, 7);

        self.hideFind()
        tr_w(self.updateButton).hide()
        self.onlyOnlineWidget.hide()
        self.takeLiveChatButton.hide()
        self.displayResendWidget(False)

        palette = self.setMainToolBarBackgroundColor(QColor(255, 193, 7))

        self.chatToolbar.setPalette(palette)
        self.filtersLayoutWidget.setPalette(palette)
        self.chatsListPage.setPalette(palette)
        self.onlyOnlineWidget.setPalette(palette)

        palette.setColor(self.mainToolbar.backgroundRole(), QColor(255, 255, 255))

        self.sendLayoutWidget.setPalette(palette)
        change_widget_background_color(self.resendWidget, QColor('#eeeeee'))

        self.mainSplitter.setPalette(palette)

        self.settingsButton.setIcon(icon_from_file("settings"))
        tr_w(self.allButton).setIcon(icon_from_file("create_group"))
        tr_w(self.groupsButton).setIcon(icon_from_file("groups"))
        tr_w(self.contactsButton).setIcon(icon_from_file("profile"))
        self.liveButton.setIcon(icon_from_file("live"))
        self.searchButton.setIcon(icon_from_file("search"))

        self.chatTypeLabel.setPixmap(pixmap_from_file("create_group", 26, 26))
        self.chatOptionsButton.setIcon(icon_from_file("three_dots"))

        self.sendButton.setIcon(icon_from_file("send"))
        self.addFileButton.setIcon(icon_from_file("dropfile"))

        self.findCancelButton.setIcon(icon_from_file("arrow_back"))

        self.closeResendButton.setIcon(icon_from_file("finish_dialog"))
        self.iconResendButton.setIcon(icon_from_file("resend"))
        self.chatCloseButton.setIcon(icon_from_file("cancel"))
        self.findInChatCloseButton.setIcon(icon_from_file("cancel"))
        self.findInChatWidget.setVisible(False)

        self.findInChatWidget.setStyleSheet(
            "QWidget#findInChatWidget{background-color: white; "
            "border-width: 1px; "
            "border-bottom-style: solid; border-right-style: none; border-top-style: none; border-left-style: none; "
            "border-color: #cccccc;}")

        conf = ChatApi.instance().conf
        userFontSize = conf.window_fontSize

        cssClassControl.add(self.toolBarLabel, "tool_bar_label")
        cssClassControl.add(self.chatTitleLabel, "tool_bar_label")
        self.changeFontSize(userFontSize)

        self.initSizes()

        self.selectChat = self.show_page_with_creating("selectChat")

        UpdateButtonDraw(self.updateButton)

        self.textEdit.setAcceptDrops(False)
        self.setAcceptDrops(True)

        self.create_page_if_not("settings")

        self.mesesForSend.init(self.textEdit)

    def initSizes(self):
        conf = ChatApi.instance().conf
        _maximized = 0
        x, y = -1, -1
        if conf:
            _chatApi = ChatApi.instance()

            x = _chatApi.conf.window_x
            y = _chatApi.conf.window_y

            _main_split_w = _chatApi.conf.window_main_split_w
            _main_split_h = _chatApi.conf.window_main_split_h
            self.mainSplitter.setSizes([_main_split_w, _main_split_h])

            _width = _chatApi.conf.window_width
            _height = _chatApi.conf.window_height
            _maximized = _chatApi.conf.window_maximized

            desktop = QApplication.desktop()
            if desktop.width() < _width:
                _width = desktop.width()
            if desktop.height() < _height:
                _height = desktop.height()

            if desktop.width() < x or desktop.height() < y:
                x = desktop.width() / 2 - _width / 2
                y = desktop.height() / 2 - _height / 2

            self.resize(_width, _height)
        else:
            self.mainSplitter.setSizes([430, 670])
            self.resize(1000, 600)

        if _maximized:
            self.showMaximized()
        else:
            if x >= 0 and y >= 0:
                self.move(x, y)

    def initStart(self):
        chatApi = ChatApi.instance()

        if chatApi.started:
            if chatApi.is_connected():
                self.showChatsList(True)
            else:
                # // FIXME
                self.showChatsList(True)
                self.setToolbarSubtitle(tr("Connecting")+"...")
                chatApi.connect()
        else:
            self.showLogin(None)

    def set_app_tunes(self, tunes):
        self.tunes = tunes

    def set_open_chat_id(self, open_chat_id):
        self._open_chat_id = open_chat_id

    def setToolbarTitle(self, text):
        self.toolBarLabel.setText(text)

    def setToolbarSubtitle(self, text): # FIXME
        if text == False:
            pass
        elif text == None or len(text) == 0:
            self.toolBarLabel.setText(ChatApi.instance().getAppName())
        else:
            self.toolBarLabel.setText(text)

    def showError(self, error):
        self.setToolbarSubtitle(error) # FIXME

    def showLogin(self, error_text=None):
        self.loginWidget = self.show_page_with_creating("login")
        self.loginWidget.showError(error_text)

    def showServer(self, error_text=None):
        serverWidget = self.show_page_with_creating("server")
        serverWidget.showError(error_text)
        serverWidget.updateValuesFromChatApi()

    def showChatsList(self, withTitle):
        self.hideKeyboard()

        if self.updateGuestMode(None, "showChatsList"):
            return None

        if withTitle:
            self.setToolbarTitle(ChatApi.instance().getAppName())
            self.setToolbarSubtitle(None)

        self.stackedWidget.setCurrentIndex(0)
        self.leftStackedWidget.setCurrentIndex(0)

    def showServerSettings(self):
        self.serverSettingsWidget = self.show_page_with_creating("serverSettings")
        ChatApi.instance().get_server_settings()

    def gotServerSettings(self, d):
        if self.serverSettingsWidget:
            self.serverSettingsWidget.gotServerSettings(d)

    def updateServerInfo(self, d):
        self.selectChat.updateServerInfo(d)

    def onAdmInfo(self, d):
        self.selectChat.updateAdmInfo(d)

    def closeAllOpenedWindows(self):
        self.selectChat = self.show_page_with_creating("selectChat")

    def showSettings(self):
        self.settingsWidget = self.show_page_with_creating("settings")
        cssClassControl.add(self.settingsWidget.label, "tool_bar_label")
        self.settingsWidget.updateNavigationDrawer()
        self.settingsWidget.setAppVersion(self.tunes.version)
        self.changeFontSize(ChatApi.instance().conf.window_fontSize)

    def showProfile(self, user_id, live_chat_id=None):
        chatApi = ChatApi.instance()
        chatApi.setCurrentChatId(-1)
        self.listView.clear_selection()
        if live_chat_id != None:
            self.profileWidget = self.show_page_with_creating("profile")
            chatApi.getUserProfile(user_id, live_chat_id=live_chat_id)
        else:
            self.profileWidget = self.show_page_with_creating("profile")
            self.profileWidget.setOpeningUserId(user_id)
            chatApi.getUserProfile(user_id)

    def showChatEditDialog(self, chat):
        self.chatEditDialog = ChatEditDialog(self, chat=chat)
        ChatApi.instance().getChatEditUsers(chat_id=chat.chat_id)
        self.chatEditDialog.exec()

    def showFileDialog(self, file_path, file_size, file_uid):
        #FileDialog = FileDialog
        if file_path == None and file_size == None:
            FileDialog.by_file_id(self, file_uid, filter_ends=('.jpg', '.png'))
        else:
            _dialog = FileDialog(self, file_path, file_size, file_uid)
            _dialog.exec()

    def makeResendWidget(self):
        chat_api = ChatApi.instance()
        resendMessage = chat_api.resendMessage
        makeResendWidgetBase(self, resendMessage)

    # @staticmethod
    # def makeResendWidgetBase(self, resendMessage):
    #     is_message = isinstance(resendMessage, Message)

    #     self.displayResendWidget(is_message)
    #     if is_message:
    #         sender = resendMessage.getSenderName()
    #         text = resendMessage.text

    #         palette = self.resendSenderLabel.palette()
    #         palette.setColor(QPalette.WindowText, QColor('#ffc107'))
    #         self.resendSenderLabel.setPalette(palette)

    #         f = self.resendMessageLabel.font()
    #         fm = QFontMetrics(f)
    #         width = self.resendMessageLabel.width()

    #         elided_text = fm.elidedText(text, Qt.ElideRight, width)
    #         self.resendSenderLabel.setText(sender)
    #         self.resendMessageLabel.setText(elided_text)

    def closeResendWidget(self):
        ChatApi.instance().setResendMessage(None)
        self.displayResendWidget(False)

    def closeCurrentChat(self):
        self.selectChat = self.show_page_with_creating("selectChat")
        self.listView.clear_selection()
        ChatApi.instance().closeCurrentChat()

    def displayResendWidget(self, need_show=False):
        if need_show:
            self.resendWidget.show()
        else:
            self.resendWidget.hide()

    def onFileProgress(self, fileId, progress, download):
        if download:
            if fileId != None and progress == 100:
                self.showFileDialog(None, None, fileId)

    def show_page_with_creating(self, name):
        page = self.pages[name]

        stacked = page["stacked"]
        stacked.setCurrentIndex(page["page"])

        self.create_page_if_not(name)

        return page["object"]

    def create_page_if_not(self, name):
        page = self.pages[name]

        if not page["object"]:
            page_widget = getattr(self, name + "Page")

            lay = QHBoxLayout(page_widget)
            lay.setContentsMargins(0, 0, 0, 0)

            w = page["cls"](page_widget, self)
            lay.addWidget(w)

            page["object"] = w


    def is_on_page(self, name):
        page = self.pages[name]
        stacked = page["stacked"]
        return stacked.currentIndex() == page["page"]

    def updateAvatars(self):
        self.updateChatsListView(source='updateAvatars')
        if self.is_on_page('profile'):
            self.profileWidget.getProfileUpdate()

    def updateProfile(self, userProfile):
        # FIXME
        if self.is_on_page('profile'):
            self.profileWidget.updateProfile(userProfile)

    def hideKeyboard(self):
        pass # FIXME

    def clearChatsList(self):
        self.updateChatsListView(clear=True, source='clearChatsList')

    def updateChatsListView(self, clear=False, start=False, source=None):
        _add = '' if source == None else ' source: {}'.format(source)
        if start:
            model = ChatsListModel(self.listView, ChatApi.instance().chats)
            model.main_widget = self
            model.set_auto_update_items(False)
            model.set_filter_control(self.filterControl)
            self.filterControl.filter()
        else:
            model = self.listView.model()
            model.updateDraws(clear=clear)

    def resizeEvent(self, QResizeEvent):
        self.resizeTextEdit()

    def textEdit_textChanged(self):
        _text = self.textEdit.toPlainText()
        _text2 = ChatApi.fix_text(_text)
        if _text != _text2:
            self.textEdit.setPlainText(_text2)
        self.resizeTextEdit()

    def findInChatEdit_textChanged(self):
        line = self.findInChatEdit.text()
        model = self.chatListView.model()
        model._find_in_chat_line = line
        self.updateMessagesShow(False)

    def showFindLine(self, val):
        self.findInChatWidget.setVisible(val)
        if val:
            self.findInChatEdit.setFocus()
        else:
            line = self.findInChatEdit.text()
            if len(line) > 0:
                self.findInChatEdit.setText('')
            self.findInChatEdit.clearFocus()

    def closeFindInChatEdit(self):
        self.showFindLine(False)

    def resizeTextEdit(self):
        max_height = 100
        base_height = getattr(self.textEdit, 'ourStyleMinHeight', 40)
        text_height = self.textEdit.document().size().height()
        slw = self.sendLayoutWidget
        slw.setMaximumSize(QSize(int(16777215), int(max(base_height, min(text_height, max_height)))))

    def connectSignals(self):
        self.textEdit.textChanged.connect(self.textEdit_textChanged)
        self.sendButton.clicked.connect(self.onSendClicked)
        self.settingsButton.clicked.connect(self.onSettingsClicked)
        self.searchButton.clicked.connect(self.onSearchClicked)
        self.findCancelButton.clicked.connect(self.onFindCancelClicked)
        self.findLineEdit.textChanged.connect(self.findLineEditTextChanged)
        self.addFileButton.clicked.connect(self.addFileClicked)
        self.textEdit.installEventFilter(self)
        tr_w(self.onlyOnlineCheckBox).toggled.connect(self.onlyOnlineToggled)
        self.chatOptionsButton.clicked.connect(self.onChatOptionsButtonClicked)
        self.updateButton.clicked.connect(self.onUpdateButtonClicked)
        self.closeResendButton.clicked.connect(self.closeResendWidget)
        self.takeLiveChatButton.clicked.connect(self.onTakeLiveChat)
        self.chatCloseButton.clicked.connect(self.closeCurrentChat)

        self.clipboard = QApplication.clipboard()
        self.clipboard.changed.connect(self.clipboardDataChanged)

        self.findInChatEdit.textChanged.connect(self.findInChatEdit_textChanged)
        self.findInChatCloseButton.clicked.connect(self.closeFindInChatEdit)

        self.messageGoodsButton.clicked.connect(self.messageGoodsClicked)

    def messageGoodsClicked(self, button=None, textEdit=None):
        if not button:
            button = self.messageGoodsButton
        if not button:
            textEdit = self.textEdit
        global_pos = button.parent().mapToGlobal(button.pos())

        menu = QMenu(self)
        boldTextAction = menu.addAction("Bold") # icon_from_file("create_group"),
        boldTextAction.triggered.connect(lambda: self.boldTextClicked(textEdit))

        smilesMenu = menu.addMenu("Smiles")

        for smile in SMILES:
            self.makeSmileAction(smilesMenu, smile, textEdit)

        if menu:
            menu.exec_(global_pos)

        return menu

    def boldTextClicked(self, textEdit=None):
        if not textEdit:
            textEdit = self.textEdit
        cursor = textEdit.textCursor()

        txt = cursor.selectedText()
        if len(txt) > 0:
            txt = '<b>' + txt + '</b>'
            cursor.insertText(txt)
        else:
            cursor.insertText('<b>')
            last_pos = cursor.position()
            cursor.insertText('</b>')
            self.setInputPosition(last_pos, textEdit)

    def makeSmileAction(self, smilesMenu, smile, textEdit):
        icon_name = SMILES_DICT.get(smile, None)
        if icon_name:
            main_icon = icon_from_file(icon_name)
            smileAction = smilesMenu.addAction(main_icon, '')
        else:
            smileAction = smilesMenu.addAction(smile)
        smileAction.triggered.connect(lambda: self.smileClicked(smile, textEdit))

    def smileClicked(self, smile, textEdit=None):
        if not textEdit:
            textEdit = self.textEdit
        cursor = textEdit.textCursor()
        cursor.insertText(smile)

    def setInputPosition(self, pos, textEdit=None):
        if not textEdit:
            textEdit = self.textEdit
        cursor = textEdit.textCursor()
        cursor.clearSelection()
        cursor.setPosition(pos)
        textEdit.setTextCursor(cursor)

    def findLineEditTextChanged(self, text):
        self.filterControl.setFindText(text)

    win_taskbar_button = None

    @tryable
    def updateBadges(self):
        self.updateButtonsBadges()

        badges_count_all = self.filterControl.badges_count_all
        badges_count_all_muted = self.filterControl.badges_count_all_muted

        from .core.draw import icon_from_file

        muted = False if badges_count_all > badges_count_all_muted else True
        tray_icon = draw_badges_on_icon(icon_from_file("favicon"), badges_count_all, only_dot=True, muted=muted)

        self.tray_icon.setIcon(tray_icon)
        # if sys.platform.startswith("win"):
        #     from win32com.shell import shell, shellcon
        #     shell.SHChangeNotify(shellcon.SHCNE_ASSOCCHANGED, shellcon.SHCNF_IDLIST, None, None)

        main_icon = QIcon() if badges_count_all <= 0 else (icon_from_file("round_muted") if muted else icon_from_file("round"))

        if sys.platform.startswith('win'):
            if self.win_taskbar_button == None:
                from PyQt5.QtWinExtras import QWinTaskbarButton
                button = QWinTaskbarButton(self)
                self.win_taskbar_button = button
            else:
                button = self.win_taskbar_button
            button.setWindow(self.windowHandle())
            button.setOverlayIcon(main_icon)

    @tryable
    def updateButtonsBadges(self):
        self.filterControl.updateButtons()

    def updateChats(self):
        self.updateChatsListView(source='updateChats')

    def updateOpenedChat(self):
        chatApi = ChatApi.instance()
        if chatApi.getCurrentChatId() >= 0 :
            currentChat = chatApi.getCurrentChat()
            if currentChat == None:
                self.closeOpenedChat()
            else:
                chat_id = currentChat.chat_id
                is_going_to_other_chat = self.showChat(chat_id, None, stay_in_chat_if_possible=True)
                if is_going_to_other_chat:
                    openStarted = ChatApi.instance().openChat(chat_id)

    def closeOpenedChat(self):
        chatApi = ChatApi.instance()
        chatApi.setCurrentChatId(-1)
        if self.rightStackedWidget.currentIndex() != 2:
            self.rightStackedWidget.setCurrentIndex(2)

    def updateMessages(self, withScrollToBottom):
        self.updateChatsListView(source='updateMessages')
        self.updateMessagesShow(withScrollToBottom)
        self.updateBadges()

    def updateMessagesShow(self, withScrollToBottom):

        model = self.chatListView.model()
        # if False and model and len(model.items_dict) > 1:
        #     model.items_dict = ChatApi.instance().current_chat_messages.messages
        #     model.update_items()
        # else:
        self.clearMessagesList(clear=True, withScrollToBottom=withScrollToBottom)

        # # withScrollToBottom and
        # if self.chatListView.need_scroll_to_bottom_on_messages:
        #     self.chatListView.scroll_to_bottom()

    def clearMessagesList(self, clear=False, withScrollToBottom=False):
        messagesList = self.chatListView
        messagesList.clearSelectionText()

        if messagesList.model() is None:
            model = MessagesDictModel(messagesList)
            model.model_item = MessageItem
        else:
            model = messagesList.model()

        model.items_dict = ChatApi.instance().current_chat_messages.messages
        model.reset_model(change_need_to_bottom=False)

    def updateNavigationDrawer(self):
        if self.settingsWidget:
            self.settingsWidget.updateNavigationDrawer()

        chatApi = ChatApi.instance()
        current_user_id = str(chatApi.getCurrentUserId())
        if self.profileWidget and self.profileWidget.openingUserId and str(self.profileWidget.openingUserId) == current_user_id:
            self.profileWidget.updateProfile(chatApi.userProfile)

    def onSendClicked(self):
        text = self.textEdit.toPlainText()
        ChatApi.instance().sendMessageSmart(text)

        self.textEdit.clear()

    def updateGuestMode(self, user_type, source=None):
        if user_type == None:
            user_type = ChatApi.instance().user_type
        if user_type == None:
            return False
        if user_type == User.USER_TYPE_GUEST:
            self.blockInGuestMode()
            return True
        else:
            self.unblockFromGuestMode(user_type)
        return False

    def blockInGuestMode(self):

        self.showSettings()

        chat = self.showFirstLiveChat()

        ChatApi.instance().setCurrentChatId(chat.chat_id)

        self.setToolbarSubtitle(None)

        self.chatOptionsButton.hide()

    def unblockFromGuestMode(self, user_type=None):
        if user_type:
            if user_type == User.USER_TYPE_MANAGER:
                self.liveButton.show()
            else:
                self.liveButton.hide()

        self.chatOptionsButton.show()

    def showFirstLiveChat(self):
        chat_api = ChatApi.instance()

        first_chat = None
        if len(chat_api.chats) > 0:
            first_chat = chat_api.chats[0] # FIXME

        for ch in chat_api.chats:
            if ch.is_live():
                first_chat = ch
                break

        self.showChatWithOpen(first_chat.chat_id)
        return first_chat

    def showChatWithOpen(self, chat_id):
        self.showChat(chat_id, None)
        openStarted = ChatApi.instance().openChat(chat_id)

    def showChat(self, chat_id, userName, stay_in_chat_if_possible=False):
        chat = None
        is_going_to_other_chat = True
        sendLayoutWidget_show = True

        #self.closeResendWidget()

        mes_model = self.chatListView.model()
        mes_model.is_only_files = False
        mes_model.is_only_favorites = False

        if chat_id != None:

            chatApi = ChatApi.instance()
            last_chat_id = chatApi.getCurrentChatId()

            chat = chatApi.getChatById(chat_id)
            chatName = chatApi.getChatName(chat_id)

            if stay_in_chat_if_possible and last_chat_id == chat_id:
                is_going_to_other_chat = False

            if is_going_to_other_chat:
                chatApi.clearCurrentChat()

            # ----------------------------
            self.takeLiveChatButton.hide()
            sendLayoutWidget_show = False
            # ----------------------------

            if chatName == None:
                chatName = ""
            if userName != None:
                chatName = userName

            AVA_SIZE = (42, 42)

            if chat:
                avatar = chat.getAvatar()
                if avatar:
                    avatar = pixmap_from_icon_rounded(avatar, to_size=AVA_SIZE)
                if not avatar:
                    ava_name = chat.getIconName()
                    if ava_name in ("user", "group"):
                        ava_name += "_black"
                    avatar = pixmap_from_file(ava_name, *AVA_SIZE)
                self.chatTypeLabel.setPixmap(avatar) #.setIcon(icon_from_file(chat.getIconName()))

                if chat and chat.is_live() and not chatApi.isUserGuest():
                    managerUser = chatApi.getUser(chat.live_manager)
                    self.managerWidget.show()
                    self.managerNameLabel.setText(managerUser.name if managerUser else "-")
                    self.managerAvatarLabel.setText("-")
                    if chat.is_mine():
                        sendLayoutWidget_show = True # self.sendLayoutWidget.show()
                    else:
                        live_manager_name = chat.live_manager_name()
                        if live_manager_name:
                            live_button_text = tr('TAKE CHAT from') + ' "{}"'.format(live_manager_name)
                        else:
                            live_button_text = tr("TAKE CHAT")
                        self.takeLiveChatButton.setText(live_button_text)
                        self.takeLiveChatButton.show()
                    if managerUser:
                        avatar = managerUser.profile.getBitmap()
                        if avatar:
                            avatar = pixmap_from_icon_rounded(avatar, to_size=(26, 26))
                    if not avatar:
                        avatar = pixmap_from_file("user_black", 26, 26)
                    self.managerAvatarLabel.setPixmap(avatar)
                else:
                    sendLayoutWidget_show = True #self.sendLayoutWidget.show()
                    self.managerWidget.hide()

            else:
                self.chatTypeLabel.setPixmap(pixmap_from_file("user_black", *AVA_SIZE)) #.setIcon(icon_from_file("user")) # FIXME hack..

            self._current_chat_name = chatName
            self.updateChatTitle()

            if is_going_to_other_chat:
                self.setToolbarSubtitle(tr("Loading"))

            self.sendLayoutWidget.setVisible(sendLayoutWidget_show)

            self.makeResendWidget()

            self.mesesForSend.updateMessageEditor(chat_id)

            # FIXME hack:
            if self.findInChatWidget.isVisible() or self.findLineEdit.isVisible:
                pass
            else:
                self.textEdit.setFocus()

        if self.rightStackedWidget.currentIndex() != 0:
            self.rightStackedWidget.setCurrentIndex(0)

        def _onChatOptionsButtonClicked(globalPos):
            chatApi = ChatApi.instance()
            _chat = chatApi.getCurrentChat()
            if _chat:
                class chat:
                    chat = _chat
                menu = self.listView.model().make_menu(chat)
                menu.exec_(globalPos)

        self._onChatOptionsButtonClicked = _onChatOptionsButtonClicked

        self.chatListView.delegate.last_load_min_message_id = None

        return is_going_to_other_chat

    def onNoConnect(self):
        if self.on_no_connect_callback:
            self.on_no_connect_callback()

    def onChatOptionsButtonClicked(self):
        rect = self.chatOptionsButton.rect()
        pos = QPoint(rect.left(), rect.bottom())
        self._onChatOptionsButtonClicked(self.chatOptionsButton.mapToGlobal(pos))

    def _onChatOptionsButtonClicked(self, pos):
        pass

    def onUpdateButtonClicked(self):
        ret = QMessageBox.question(self, tr("Update"),
                                   tr("You can be updated. Do you want to restart application now?"),
                                   QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            ChatApi.start_update_clicked()
            # WARNING: do not write update code here, only in method "ChatApi.start_update_clicked" !!!
        else:
            pass

    def tryCurrentChatEdit(self):
        return self.chatEditDialog

    def onSettingsClicked(self):
        self.showSettings()

    def onTakeLiveChat(self):
        chat = ChatApi.instance().getCurrentChat()
        if chat and chat.is_live():
            ChatApi.instance().take_live_chat(chat.chat_id)

    def addFileClicked(self):
        filename, ok = QFileDialog.getOpenFileName(self, tr("Choose file"), get_download_path())
        if filename:
            self.send_file(filename)

    def show_smart_info(self, smart_text):
        if smart_text == None or len(smart_text) == 0:
            self.smartTextLabel.hide()
        else:
            self.smartTextLabel.setText(smart_text)
            self.smartTextLabel.show()

    def applyBadges(self, badgesCount):
        boo = self.filterControl.setAllBadgesCount(badgesCount)
        if boo:
            self.updateBadges()

    def onSearchClicked(self):
        self.showFind()

    def onFindCancelClicked(self):
        self.hideFind()

    def showFind(self):
        self.settingsButton.hide()
        self.toolBarLabel.hide()
        self.searchButton.hide()
        self.findLineEdit.show()
        self.findCancelButton.show()
        self.setMainToolBarBackgroundColor(QColor(255, 255, 255))
        self.findLineEdit.setFocus()

    def hideFind(self):
        self.findLineEdit.setText("")
        self.findLineEdit.hide()
        self.findCancelButton.hide()
        self.settingsButton.show()
        self.toolBarLabel.show()
        self.searchButton.show()
        self.setMainToolBarBackgroundColor(QColor(255, 193, 7))
        self.findLineEdit.clearFocus()

    def showInputCall(self, text):
        if not self.input_call_widget:
            self.input_call_widget = InputCallWidget(None)
        self.input_call_widget.fill(text)
        self.input_call_widget.show()
        self.input_call_widget.move(0, 0)
        self.input_call_widget.raise_()

    def setMainToolBarBackgroundColor(self, color):
        return change_widget_background_color(self.mainToolbar, color)

    @by_timer(1)
    @tryable
    def loadUpdatePack(self, ver):
        ret, txt = Updater.prepare_update(ver)
        #ret, txt = -1, "!!!! Some test text (loadUpdatePack) ..."
        if ret == 0:
            ChatApi.instance().callbacks.onNeedshowUpdateButton()
        elif txt:
            ChatApi.instance().callbacks.needShowSmartInfo(txt)

    def showUpdateButton(self, d=None):
        for ub in self.genUpdateButtons():
            ub.show()
            ub.setProgress(0)

    def setUpdateProgress(self, progress):
        for ub in self.genUpdateButtons():
            if progress > 0 and not ub.isVisible():
                ub.show()
            ub.setProgress(progress)

    def genUpdateButtons(self):
        for w in (self, self.loginWidget):
            if w:
                yield w.updateButton

    def closeNow(self):
        self.MAY_CLOSE_NOW = True
        self.close()

    def closeEvent(self, e):
        _size = self.size()
        _pos = self.pos()
        _sizes = self.mainSplitter.sizes()

        conf = ChatApi.instance().conf
        _maximized = int(self.isMaximized())
        if conf:
            conf.window_main_split_w = _sizes[0]
            conf.window_main_split_h = _sizes[1]
            if not _maximized:
                conf.window_width = _size.width()
                conf.window_height = _size.height()
                conf.window_x = _pos.x()
                conf.window_y = _pos.y()
            conf.window_maximized = _maximized
            #conf.save()

        if not hasattr(self, "MAY_CLOSE_NOW"):
            if self.on_want_close_callback:
                if not self.on_want_close_callback():
                    e.ignore()
                    return
            elif self.isActiveWindow():
                ans = QMessageBox.question(self, tr("Exiting from {}").format(
                    APP_TITLE
                ), tr("Are you sure you want to close the application?\n\nYou can simply minimize it, if not."), QMessageBox.Close, QMessageBox.Cancel)
                need_close = ans==QMessageBox.Close
                if not need_close:
                    e.ignore()
                    return

        if self.input_call_widget:
            self.input_call_widget.close()

        chatApi = ChatApi.instance()
        chatApi.finish()
        chatApi.savePrefs()

        if self.tray_icon:
            self.tray_icon.close()

        ret = super().closeEvent(e)
        return ret

    def information(self, text):
        QMessageBox.information(self, tr("Information {}").format(
                    APP_TITLE
                ), tr(text))

    def showEvent(self, e):
        return super().showEvent(e)

    def changeEvent(self, e):
        if e.type() == QEvent.WindowStateChange:
            if self.isMaximized():
                self.was_maximized = True
            elif self.isMinimized():
                pass
            else:
                self.was_maximized = False
        return super().changeEvent(e)

    def event(self, e):
        if e.type() == QEvent.WindowActivate:
            ChatApi.instance().setGuiVisible(True)
        elif e.type() == QEvent.WindowDeactivate:
            ChatApi.instance().setGuiVisible(False)
        return super().event(e)

    def dragEnterEvent(self, e):
        if (e.mimeData().hasUrls()):
            e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            filename = url.toLocalFile()
            self.send_file(filename)

    def send_file(self, filename):
        ChatApi.instance().sendFile({
            'uri': filename,
            'fileName': basename(filename),
            'fileSize': getsize(filename)
        })

    def onlyOnlineToggled(self, *args):
        self.filterControl.updateButtons()

    def show_notify(self, message, title=APP_TITLE, second_title=""):
        if second_title:
            title = title + ": " + second_title
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.NoIcon) # FIXME: QIcon("data/images/favicon.png"))

    def clipboardDataChanged(self, mode):
        pass

    def eventFilter(self, object, event):
        if object == self.textEdit:
            if event.type() == QEvent.KeyPress:

                is_key_enter = (event.key() == Qt.Key_Enter) or (event.key() == Qt.Key_Return)

                is_enter = is_key_enter
                is_enter_with_ctrl = (is_enter and event.modifiers() == Qt.ControlModifier) or (is_enter and event.modifiers() == Qt.ShiftModifier)
                if is_enter_with_ctrl:
                    self.textEdit.insertPlainText("\n")
                    return True
                elif is_enter:
                    self.onSendClicked()
                    return True
                else:
                    if self.keyPressEvent(event, with_return=True):
                        return True

        elif object == self.chatTitleLabel:
            if event.type() == QEvent.Resize:
                self.updateChatTitle()


        return super().eventFilter(object, event)

    def updateChatTitle(self):
        chatName = self._current_chat_name
        if chatName:
            chatName = chatName.replace('\n', ' ')
            w = self.chatTitleLabel.width()
            max_len = int(w / 12)

            if len(chatName) > max_len:
                chatName = chatName[:max_len - 3] + '...'

        self.chatTitleLabel.setText(chatName)

    def keyPressEvent(self, event, with_return=False):
        has_ctrl = event.modifiers() == Qt.ControlModifier
        is_v = event.key() == Qt.Key_V

        self.setSelectionOnChatListView(has_ctrl)

        if is_v and has_ctrl:
            ret = self.pasteEvent()
            if with_return:
                return ret

        if event.type() == QKeyEvent.KeyPress:
            if event.matches(QKeySequence.Copy):
                self.copyEvent.emit()

    def keyReleaseEvent(self, event):
        has_ctrl = event.modifiers() == Qt.ControlModifier
        self.setSelectionOnChatListView(has_ctrl)

    def pasteEvent(self):
        mimeData = self.clipboard.mimeData()
        if mimeData.hasImage():
            image = mimeData.imageData()
            ChatApi.instance().sendFile(None, image=image)
            return True

        elif mimeData.hasHtml():
            pass
        elif mimeData.hasText():
            _text = mimeData.text()
            if _text.startswith("file://"):
                _text = _text[len("file://"):]
                if sys.platform.startswith("win") and _text.startswith("/"):
                    _text = _text[1:]
                ChatApi.instance().sendFile(None, filepath=_text)
                return True
        else:
            pass

    def setSelectionOnChatListView(self, allow_selection):
        if allow_selection:
            self.chatListView.setSelectionMode(QAbstractItemView.MultiSelection)
        else:
            self.chatListView.setSelectionMode(QAbstractItemView.NoSelection)

    def changeFontSize(self, _userFontSize):
        userFontSize = _userFontSize
        if userFontSize not in (1, 2, 3) or "preview" not in sys.argv:
            userFontSize = 1
        if userFontSize:
            css_classes = {}
            if userFontSize == 1:
                self.textEdit.ourStyleMinHeight = 40
                self.setStyleSheet(
                    FULL_STYLESHEET+"""
                    QLineEdit {font-family: Arial; font-size: 12pt;}
                    QTextEdit {font-family: Arial; font-size: 12pt; min-height: 38px;}
                    sendLayoutWidget{min-height: 40px;}
                    QListView {font-size: 10pt;}
                    QLabel {font-size: 10pt;}
                    QToolButton {font-size: 10pt;}
                    """
                )
                css_classes['tool_bar_label'] = "font-size: 16pt;"
            elif userFontSize == 2:
                self.textEdit.ourStyleMinHeight = 60
                self.setStyleSheet(
                    FULL_STYLESHEET+"""
                    QLineEdit {font-family: Arial; font-size: 18pt;}
                    QTextEdit {font-family: Arial; font-size: 18pt; min-height: 57px;}
                    sendLayoutWidget{min-height: 60px;}
                    QListView {font-size: 18pt;}
                    QLabel {font-size: 14pt;}
                    QToolButton {font-size: 15pt;}
                    """
                )
                css_classes['tool_bar_label'] = "font-size: 24pt;"
            elif userFontSize == 3:
                self.textEdit.ourStyleMinHeight = 80
                self.setStyleSheet(
                    FULL_STYLESHEET+"""
                    QLineEdit {font-family: Arial; font-size: 24pt;}
                    QTextEdit {font-family: Arial; font-size: 24pt; min-height: 76px;}
                    sendLayoutWidget{min-height: 80px;}
                    QLabel {font-size: 18pt;}
                    QListView{font-family: Arial; font-size: 24pt;}
                    QToolButton {font-size: 20pt; }
                    """
                )
                css_classes['tool_bar_label'] = "font-size: 32pt;"
            cssClassControl.update_style(css_classes)
        else:
            self.setStyleSheet(FULL_STYLESHEET)
        self.resizeTextEdit()

