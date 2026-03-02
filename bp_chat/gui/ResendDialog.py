
from copy import deepcopy

from PyQt5.QtWidgets import QDialog, QAbstractItemView, QMessageBox
from PyQt5.QtCore import Qt #, WindowFlags
from PyQt5.QtGui import QColor, QPainter

from .ui.UiResendDialog import Ui_ResendDialog

from .delegates.ChatsListDelegate import ChatsListModel

# from ..logic.datas.GroupChat import GroupChat
from ..logic.chat_api.ChatApi import ChatApi

from .views.ChatsListView import _ChatsListView
from bp_chat.gui.common.draw_funcs import makeResendWidgetBase
from bp_chat.gui.core.draw import icon_from_file
from .models.model_items import ChatItem
from bp_chat.gui.common.langs import tr_w, tr
from bp_chat.gui.views.FilterButtonControl import FilterButtonsControl
from bp_chat.gui.models.element_parts import *


P_DEBUG = False


class ChatsListForResendView(_ChatsListView):

    def open_menu_for_selected_item(self, global_pos):
        pass

    def _selected_callback(self, selected):
        self.model()._selected_callback(selected)


class ChatsListForResendModel(ChatsListModel):

    selected_item = None
    dialog = None

    _PARTS = PChatLayout(
        PChatImage(margin_left=8, margin_top=8, margin_right=8),
        PVLayout(
            PStretch(),
            PHLayout(PLogin(debug=P_DEBUG), PChatMuted(debug=P_DEBUG), PChatPinned(debug=P_DEBUG), PLastTime(debug=P_DEBUG)),
            PLastMessage(margin_top=5, debug=P_DEBUG),
            PStretch(),
            PChatDownLine(debug=P_DEBUG),
            margin_right=10
        ), debug=P_DEBUG
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.delegate._PARTS = self._PARTS
        # self._PARTS.childs[0]._custom_x = 30
        # self._PARTS.childs[0]._custom_y = 30

    def _selected_callback(self, selected):
        if selected and len(selected) > 0:
            self.selected_item = selected[0]
            self.dialog.pushButtonOk.setVisible(True)

    def check_item_is_selected(self, item):
        return self.selected_item != None and item == self.selected_item


class ResendDialog(QDialog, Ui_ResendDialog):

    chat = None
    group_users = []

    def __init__(self, main_widget=None, message=None, flags=Qt.Window, *args, **kwargs):
        self.mw = main_widget
        self.message = message
        super().__init__(main_widget)

        self.setupUi(self)
        self.retranslateUi(self)

        self.initListView()
        self.connectSignals()

        self.resize(500, 800)

    def initListView(self):
        self.filter_control = FilterButtonsControl(allButton=True, groupsButton=None, contactsButton=None, liveButton=None, main_widget=self.mw)

        self.listView.hide()

        tr_w(self.label)
        self.setWindowTitle(tr(self.windowTitle()))

        tr_w(self.inputChat, placeHolder=True)
        tr_w(self.pushButtonOk)
        tr_w(self.pushButtonCancel)

        self.closeResendButton.setIcon(icon_from_file("finish_dialog"))
        self.iconResendButton.setIcon(icon_from_file("resend"))

        self.pushButtonOk.setVisible(False)

        newListView = ChatsListForResendView(self)
        newListView.setFont(self.listView.font())
        newListView.setFrameShape(self.listView.frameShape())
        newListView.setVerticalScrollMode(self.listView.verticalScrollMode())
        newListView.setHorizontalScrollMode(self.listView.horizontalScrollMode())
        newListView.setSelectionMode(QAbstractItemView.MultiSelection)
        self.verticalLayout.replaceWidget(self.listView, newListView)
        self.listView = newListView
        self.updateListView(start=True)

        makeResendWidgetBase(self, self.message, displayResendWidget=False, custom_width=300)

        flags = self.windowFlags()
        flags = int(flags)
        flags &= ~Qt.WindowContextHelpButtonHint
        flags = Qt.WindowFlags(flags)
        self.setWindowFlags(flags)

        self.setStyleSheet(
            """
            QLineEdit {font-family: Arial; font-size: 12pt;}
            QTextEdit {font-family: Arial; font-size: 12pt; min-height: 70px;}
            QListView {font-size: 10pt;}
            QLabel {font-size: 10pt;}
            QToolButton {font-size: 10pt;}
            """
        )
        self.iconResendButton.hide()
        self.closeResendButton.hide()

    def connectSignals(self):
        self.inputChat.textChanged.connect(self.inputChatTextChanged)
        self.pushButtonOk.clicked.connect(self.accept)
        self.pushButtonCancel.clicked.connect(self._reject)
        self.messageGoodsButton.clicked.connect(lambda: self.mw.messageGoodsClicked(self.messageGoodsButton, self.textEdit))
        self.textEdit.textChanged.connect(self.textEdit_textChanged)

    def updateListView(self, clear=False, start=False, filter_text=""):
        filter_text = self.inputChat.text()
        self.filter_control.setFindText(filter_text)
        self.filter_control.filter()

        model = ChatsListForResendModel(self.listView, self.filter_control.chats)
        model.dialog = self
        self.listView.setModel(model)
        self.listView.update_items_indexes()

    def inputChatTextChanged(self):
        self.updateListView()

    def textEdit_textChanged(self):
        _text = self.textEdit.toPlainText()
        _text2 = ChatApi.fix_text(_text)
        if _text != _text2:
            self.textEdit.setPlainText(_text2)

    def accept(self):
        selected_chat_item = self.listView.model().selected_item
        selected_chat = selected_chat_item.chat

        chat_api = ChatApi.instance()
        chat_id_tmp = chat_api.getCurrentChatId()
        chat_api.setCurrentChatId(selected_chat.chat_id)
        chat_api.setResendMessage(self.message)
        chat_api.sendMessageSmart(self.textEdit.toPlainText())
        chat_api.setCurrentChatId(chat_id_tmp)

        self._reject()

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_Escape:
            self._reject()
        elif key_event.key() == Qt.Key_Return:
            self.accept()

    def _reject(self):
        self.reject()
        self.deleteLater()