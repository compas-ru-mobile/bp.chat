
from datetime import datetime

import webbrowser

from PyQt5.QtWidgets import QWidget, QItemDelegate, QStyle, QStyledItemDelegate, QAbstractItemView, QMenu
from PyQt5.QtGui import (QColor, QPainter, QIcon, QPen, QTextDocument, QAbstractTextDocumentLayout, QCursor,
                         QFontMetrics, QFont, QFontDatabase, QGuiApplication)
from PyQt5.QtCore import Qt, QAbstractListModel, QSize, QPointF, QRect, QRectF, QPoint, pyqtSignal, QItemSelectionModel, QItemSelection

from ...logic.chat_api.ChatApi import ChatApi
from ...logic.chat_api.DeliveredSender import DeliveredSender
from ...logic.chat_api import ChatApiCommon
from ...logic.datas.Message import Message
from ..core.draw import pixmap_from_icon_rounded, icon_from_file
from ..paint.MessageDrawer import MessageDrawer
from ..paint.Selection import Selection
from bp_chat.gui.paint.Word import WORD_TYPE_LINK
from bp_chat.gui.paint.Line import LINE_TYPE_FILE

from threading import Timer
from os.path import exists, join
from copy import copy

from ..models.model_items import MessageItem
from ..models.list_model import MessagesListDelegate, MessagesListModel, LoadMessagesButton
from ...core.app import App
from bp_chat.gui.common.langs import tr
from ...core.local_db_messages import LocalDbMessagesMap
from bp_chat.logic.chat_api.ChatApiCommon import in_thread, by_timer

from bp_chat.gui.ResendDialog import ResendDialog

LoadMessagesButton.text = tr(LoadMessagesButton.text)


class MessagesDictModel(MessagesListModel):

    deliveredSender = None
    updateLast1000 = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mw.copyEvent.connect(self.onCopyTextByCtrlC)

        self.deliveredSender = DeliveredSender.getInstance()

        self.updateLast1000.connect(self.updateLast1000Slot)

    def get_current_user_id(self):
        return ChatApi.instance().getCurrentUserId()

    def on_need_download_20(self, min_message_id):
        ChatApi.instance().getLastMessagesOnCurrentChat(min_message_id)

    def getItemPixmap(self, message):

        message = message.message

        avatar_d = self.delegate.image_width()
        avatar_r = avatar_d / 2

        # аватар - изображение
        user = message.getSender()
        btm = None
        if user:
            up = user.profile
            btm = up.getBitmap()
        offset_x = offset_y = 0  # FIXME hack
        pixmap = None
        if btm:
            pixmap = pixmap_from_icon_rounded(btm, to_size=(avatar_d, avatar_d))
            if pixmap:
                offset_x = (pixmap.width() - avatar_d) / 2
                offset_y = (pixmap.height() - avatar_d) / 2
        if not pixmap:
            icon = icon_from_file("user")
            pixmap = icon.pixmap(QSize(int(avatar_d), int(avatar_d)))

        return pixmap

    def prepare_selected_messages(self):
        return [ind.item for ind in self.listView._current_selection] if self.listView._current_selection else []

    def make_menu(self, message_item):
        menu = QMenu(self.listView)
        _selected_messages = self.prepare_selected_messages()

        #self.update_selected_messages()

        on_message = message_item.message if message_item else None
        if on_message and hasattr(message_item.message, 'NOT_MESSAGE'):
            on_message = None

        ln_add = ''
        if on_message:
            if len(_selected_messages) == 0:
                _selected_messages = [on_message]

            ln = len(_selected_messages) #if not _selected_messages or len(_selected_messages) == 1 else len(_selected_messages)
            ln_add = '' if ln == 1 else f' ({ln})'

            answerAction = menu.addAction(icon_from_file("resend"), tr("Answer") + ln_add)
            answerAction.triggered.connect(lambda: self.onCreateAnswerMessage(_selected_messages))

            resendAction = menu.addAction(icon_from_file("arrow_back"), tr("Resend") + ln_add)
            resendAction.triggered.connect(lambda: self.onCreateResendMessage(_selected_messages))

            copyAction = menu.addAction(icon_from_file("file"), tr("Copy") + ln_add)
            copyAction.triggered.connect(lambda: self.onCopyText(_selected_messages))

            if not _selected_messages or len(_selected_messages) == 1:
                message_in_favorites = ChatApi.instance().is_message_in_favorites(on_message.mes_id)
                fav_name = 'From favorites' if message_in_favorites else 'To favorites'
                favAction = menu.addAction(icon_from_file("star"), tr(fav_name))
                favAction.triggered.connect(lambda: self.onFavoriteAction(fav_name.split(' ')[0].lower(), on_message.mes_id))

            # delAction = menu.addAction(icon_from_file("del"), tr("Delete message") + ln_add)
            # delAction.triggered.connect(lambda: self.onDeleteMessage(_selected_messages))

        findInChatAction = menu.addAction(tr("Find in chat") if len(self.find_in_chat_line)==0 else tr("Clear find in chat"))
        findInChatAction.triggered.connect(lambda: self.onFindInChatAction())

        if not self.is_only_files:
            onlyFilesAction = menu.addAction(tr("Show only files"))
            onlyFilesAction.triggered.connect(lambda: self.onOnlyFilesAction())

        if not self.is_only_favorites:
            onlyFavoritesAction = menu.addAction(tr("Show only favorites"))
            onlyFavoritesAction.triggered.connect(lambda: self.onOnlyFavoritesAction())

        if self.is_only_files or self.is_only_favorites:
            showAllAction = menu.addAction(tr("Show all"))
            showAllAction.triggered.connect(lambda: self.onShowAllAction())

        return menu

    def is_message_in_favorites(self, mes):
        return ChatApi.instance().is_message_in_favorites(mes.mes_id)

    def message_has_text(self, mes, text):
        return (text.lower() in mes.text.lower()) if mes else False

    def onCreateAnswerMessage(self, _selected_messages):
        #self.onCreateResendMessage(_selected_messages, other_chat=False)
        text = _selected_messages[0].text
        ChatApi.instance().setResendMessage(_selected_messages[0])

        self.mw.makeResendWidget()

    def onCreateResendMessage(self, _selected_messages, other_chat=True):
        text = _selected_messages[0].text
        #ChatApi.instance().setResendMessage(_selected_messages[0], other_chat)

        self.mw.resend_dialog = ResendDialog(self.mw, _selected_messages[0])
        self.mw.resend_dialog.exec()

        # if other_chat:
        #     self.mw.information("Please choose chat, where to resend message")

    def onCopyTextByCtrlC(self):
        #self._menu_pos = None
        selected_messages = self.prepare_selected_messages()
        if not selected_messages:
            return
        self.onCopyText(selected_messages)

    def onCopyText(self, _messages):
        #_messages = self._selected_messages if self._selected_messages else []

        lines = []
        ln = len(_messages)

        if ln == 1:
            selection_text = _messages[0].selected_text
            if not selection_text or len(selection_text.strip()) == 0:
                selection_text = _messages[0].get_text()
                quote_text = _messages[0].get_quote_text()
                if quote_text and len(quote_text.strip()) > 0:
                    quote_sender = _messages[0].quote.getSenderName()
                    quote_sender = '>> [ {} ]:\n'.format(quote_sender) if quote_sender else ''
                    selection_text = quote_sender + '>> ' + '\n>> '.join(quote_text.split('\n')) + '\n' + selection_text

        else:
            need_sender = ln > 1
            for m in sorted(_messages, key=lambda m:m.id):

                mes: Message = m
                text = mes.get_text()

                if need_sender:
                    text = '[ {} {} ]:\n'.format(mes.getSenderName(), mes.getTimeString()) + text

                lines.append(text)

            selection_text = '\n\n'.join(lines)

        self._setTextInClipboard(selection_text)

        self.listView.clear_selection()

    def onDeleteMessage(self, _messages):
        ln = len(_messages)
        lst = []
        for m in sorted(_messages, key=lambda m:m.id):
            mes: Message = m
            lst.append(mes.mes_id)
        ChatApi.instance().deleteMessages(lst)

    def onFavoriteAction(self, fav_name, mes_id):
        chat_api = ChatApi.instance()
        server_connect_config = chat_api.server_connect_config
        if server_connect_config and mes_id != None:
            LocalDbMessagesMap.set_message_favorite(
                chat_api.server_uid, mes_id, 1 if fav_name == 'to' else 0)
            self.mw.updateMessagesShow(True)

    def onOnlyFilesAction(self):
        self.is_only_files = True
        self.mw.updateMessagesShow(True)
        #self.askForLast1000messages()

    def onOnlyFavoritesAction(self):
        self.is_only_favorites = True
        self.askForLast1000messages(only='favorite')
        self.mw.updateMessagesShow(True)

    def onShowAllAction(self):
        self.is_only_files = False
        self.is_only_favorites = False
        self.mw.updateMessagesShow(True)

    #@in_thread
    #@by_timer(1)
    def askForLast1000messages(self, only=None):
        chat_api = ChatApi.instance()
        chat_id = chat_api.getCurrentChatId()
        if chat_id >= 0:
            max_id = chat_api.getMessagesFromLocalDb(chat_id, range=100, with_update_gui=False, only=only)
            return max_id
            # if max_id:
            #     self.UpdateAfterAskForLast1000messages()

    #@by_timer(1)
    def UpdateAfterAskForLast1000messages(self):
        #ChatApi.instance().updateChatMessagesGui()
        self.updateLast1000.emit()

    def updateLast1000Slot(self):
        ChatApi.instance().updateChatMessagesGui()

    def onFindInChatAction(self):
        find_line = self.find_in_chat_line
        val = True
        if len(find_line) > 0:
            self.find_in_chat_line = ''
            val = False
        self.needShowFindLine(val)

    def needShowFindLine(self, val):
        self.mw.showFindLine(val)

    @property
    def mw(self):
        return App.instance().main_widget

    def _setTextInClipboard(self, text):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)

    def add_to_delivered_by_gui(self, mes_id):
        self.deliveredSender.add_by_gui(mes_id)

    def on_need_download_file(self, file_uuid, filename):
        ChatApi.instance().downloadFile(file_uuid, filename)

    def on_need_open_file(self, file_path, filesize, file_uuid):
        self.mw.showFileDialog(file_path, filesize, file_uuid)

    def on_chat_event(self, event, *args, **kwargs):
        if event == 'INPUT_CALL':
            if ChatApi.instance().callbacks != None:
                ChatApi.instance().callbacks.onInputCall(args[0])

    def isOpeningChat(self):
        return ChatApi.instance().opening_chat_id >= 0

    def new_message_text(self):
        return tr("New message")

    def on_avatar_click(self, message):
        chat_api = ChatApi.instance()
        chat_api.on_chat_selected(message.sender.chat)


class MessagesDictDelegate(MessagesListDelegate):

    LINK_COLOR = '#0078d7'
    LINK_COLOR_HOVER = '#3397d7'
    RESEND_COLOR = '#3078ab'
    TEXT_COLOR = '#333333'
    TEXT_WHITE_COLOR = '#FFFFFF'
    INFO_COLOR = '#808080'

    avatar_r = 20
    padding_x = 10
    padding_y = 10
    spacing = 10

    deliveredSender = None
    mouse_pos = (-1, -1)
    _selection: Selection = None

    last_load_min_message_id = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_item = MessageItem

