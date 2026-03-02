
from PyQt5.QtWidgets import QItemDelegate, QMenu
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtCore import QAbstractListModel, QSize, QPointF, QRectF, pyqtSignal
from threading import Timer

from ...logic.chat_api.ChatApi import ChatApi
from ..core.draw import (draw_badges, pixmap_from_file, pixmap_from_icon, get_round_mask,
                                 pixmap_from_icon_rounded, color_from_hex, icon_from_file, draw_icon_from_file)

from bp_chat.gui.models.list_model import ChatsModel
from ..models.model_items import ChatItem
from ..ChatEditDialog import ChatEditDialog
from bp_chat.gui.common.langs import tr
from bp_chat.core.tryable import ConsoleThread


class ChatsListModel(ChatsModel):

    filterControl = None
    _main_widget = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_item = ChatItem

    @property
    def main_widget(self):
        return self._main_widget

    @main_widget.setter
    def main_widget(self, value):
        self._main_widget = value

    def getMuted(self, chat):
        if chat and chat.chat:
            return chat.chat.is_chat_muted()

    def getPinned(self, chat):
        chatApi = ChatApi.instance()
        return chatApi.is_chat_pinned(chat.chat.chat_id)

    def getItemName(self, item):
        return item.getName()

    def getItemSecondText(self, chat):
        if chat.chat.last_message:
            chatApi = ChatApi.instance()

            _text = self.fix_text_a(chat.chat.last_message.text[:1024])

            if _text is None or not _text.strip():
                if chat.chat.last_message.quote and chat.chat.last_message.quote.message:
                    _text_q = chat.chat.last_message.quote.message[:1024]
                    _text = ">> " + self.fix_text_a(_text_q)
                else:
                    _text = ""

            if chat.chat.is_group() or chat.chat.is_live() or (
                    chat.chat.last_message.sender_id != None and str(chatApi.getCurrentUserId()) == str(chat.chat.last_message.sender_id)):

                senderName = chat.chat.last_message.getSenderName()
                if senderName != None:
                    _text = senderName + ": " + _text
                else:
                    pass

            if '<b>' in _text:
                _text = _text.replace('<b>', '')
            if '</b>' in _text:
                _text = _text.replace('</b>', '')

            return _text
        return ""

    bad = False

    def fix_text_a(self, text):
        #return text
        # print(len(text))
        # print(text)
        if self.bad:
            return ' '
        try:
            return text.replace('href=', 'hrf=').replace('<a ', '(a ').replace('alert(', 'al_ert(')
        except BaseException as e:
            self.bad = True
            print(e)
            #print(text)
            return ' '

    def getItemTimeString(self, chat):
        if chat.chat.last_message:
            return chat.chat.last_message.getTimeString()

    def getItemPixmap(self, chat):
        pixmap = None

        if chat.chat.is_private():
            up = chat.chat.user.profile
            btm = up.getBitmap()
            if btm:
                pixmap = pixmap_from_icon_rounded(btm, to_size=(50, 50))
                if pixmap:
                    sz = pixmap.size()
                    _w2, _h2 = sz.width(), sz.height()
                    if _w2 > _h2:
                        _image_left_add = - int((_w2 - _h2)/2)

        if not pixmap:
            icon_name = chat.chat.getIconName()
            if icon_name:
                pixmap = pixmap_from_file(icon_name, 50, 50)

        return pixmap

    # def getItemColor(self, chat):
    #     return chat.chat_color

    def getItemStatusColor(self, chat):
        if chat.chat.is_private():
            if chat.chat.user.is_online():
                if chat.chat.user.is_sleep():
                    return QColor(249, 177, 53)
                else:
                    return QColor(84, 213, 84)
            else:
                return QColor(190, 190, 190)
        return None

    def getItemBadgesCount(self, chat):
        return chat.chat.get_badges_count()

    def getRightAdd(self):
        return 0 #return self.delegate.listView.width_add   FIXME width_add

    def updateDraws(self, *args, **kwargs):
        self.filterControl.filter()
        self.items_dict = { i:ch for i, ch in enumerate(self.filterControl.chats) }
        self.reset_model() #return super().updateDraws()

    def set_filter_control(self, filterControl):
        self.filterControl = filterControl
        self.filterControl.set_filter_starter(self.updateDraws)

    def customDraw(self, painter, chat, left_top_right_bottom, main_draw_results):

        left, top, right, bottom = left_top_right_bottom
        time_string_left, right_add = main_draw_results

        pin_left = (time_string_left - 20) if time_string_left > 0 else right - 28 + right_add
        pin_top = top + 8 + 6

        if ChatApi.instance().is_chat_pinned(chat.chat.chat_id):
            draw_icon_from_file(painter, 'pin_grey', pin_left, pin_top)
            pin_left -= 16
        if chat.chat.is_chat_muted():
            draw_icon_from_file(painter, 'mute_grey', pin_left, pin_top)

        if hasattr(chat.chat, 'user'):
            _user = chat.chat.user
            devices = _user.devices

            fin_add = ' '.join(['{} ({})'.format(ver, platform) for ver, platform in devices]) if devices else None
            if fin_add:
                font = painter.font()
                font.setPixelSize(10)
                painter.setFont(font)
                painter.drawText(left + 60, top + 10, fin_add)

    def make_menu(self, chat_item):
        chat = chat_item.chat if chat_item else None

        menu = QMenu(self.delegate.listView)

        createGroupAction = menu.addAction(icon_from_file("create_group"), tr("Create group"))
        createGroupAction.triggered.connect(self.onCreateGroupAction)
        is_admin = ChatApi.instance().is_admin

        if chat:
            if chat.is_private():
                profileAction = menu.addAction(icon_from_file("profile"), tr("Edit user") if is_admin else tr("Show profile"))
                profileAction.triggered.connect(lambda: self.onProfileAction(chat.user.id))

                if is_admin:
                    disUsAction = menu.addAction(icon_from_file("disconnect"), tr("Disconnect user"))
                    disUsAction.triggered.connect(lambda: self.onDisconnectUserAction(chat.user.id))

            elif chat.is_group():
                profileAction = menu.addAction(icon_from_file("edit"), tr("Edit group"))
                profileAction.triggered.connect(lambda: self.onChatEdit(chat))

                deleteAction = menu.addAction(icon_from_file("delete"), tr("Remove group"))
                deleteAction.triggered.connect(lambda: self.onRemoveEdit(chat))

                if chat.cochat >= 0:
                    cochatAction = menu.addAction(icon_from_file("cochat"), tr("Open co-chat"))
                    cochatAction.triggered.connect(lambda: self.onOpenCoChat(chat))

            elif chat.is_live():
                if chat.is_mine():
                    finAction = menu.addAction(icon_from_file("finish_dialog"), tr("Finish live chat"))
                    finAction.triggered.connect(lambda: self.onFinishLiveChat(chat))
                    if chat.cochat >= 0:
                        cochatAction = menu.addAction(icon_from_file("cochat"), tr("Open co-chat"))
                        cochatAction.triggered.connect(lambda: self.onOpenCoChat(chat))
                    else:
                        cochatAction = menu.addAction(icon_from_file("cochat"), tr("Create co-chat"))
                        cochatAction.triggered.connect(lambda: self.onCreateCoChat(chat))
                else:
                    takeAction = menu.addAction(icon_from_file("take"), tr("Take live chat"))
                    takeAction.triggered.connect(lambda: self.onTakeLiveChat(chat))
                if is_admin:
                    profileAction = menu.addAction(icon_from_file("profile"), tr("Edit guest"))
                    profileAction.triggered.connect(lambda: self.onProfileAction(user_id=None, live_chat_id=chat.chat_id))
                    grAction = menu.addAction(icon_from_file("edit"), tr("Edit group"))
                    grAction.triggered.connect(lambda: self.onChatEdit(chat))

        updateAction = menu.addAction(icon_from_file("refresh"), tr("Refresh chats"))
        updateAction.triggered.connect(self.onUpdateAction)

        if chat:
            chat_api = ChatApi.instance()
            chat_muted = chat.is_chat_muted()
            chat_pinned = chat_api.is_chat_pinned(chat.chat_id)

            mute_name = 'Unmute' if chat_muted else 'Mute'
            muteAction = menu.addAction(icon_from_file(mute_name.lower()), tr(mute_name))
            muteAction.triggered.connect(lambda: self.onMuteAction(mute_name.lower(), chat.chat_id))

            filtered_by_last_readed = [False]
            def is_filtered_by_last_readed(boo):
                filtered_by_last_readed[0] = boo

            badges_count = chat.get_badges_count(is_filtered_by_last_readed=is_filtered_by_last_readed)
            if badges_count > 0:
                markAllReadAction = menu.addAction(icon_from_file("all_read"), tr("Mark all read"))
                markAllReadAction.triggered.connect(lambda: self.onMarkAllReadAction(chat))
            elif chat.marked_last > 0: #filtered_by_last_readed[0]:
                unmarkAllReadAction = menu.addAction(icon_from_file("remove_all_read"), tr("Unmark all read"))
                unmarkAllReadAction.triggered.connect(lambda: self.onMarkAllReadAction(chat, unmark=True))

            if chat_pinned:
                delFromPinned_Action = menu.addAction(icon_from_file("pinned"), tr("Remove from pinned"))
                delFromPinned_Action.triggered.connect(lambda: self.onDelFromPinned_Action(chat))
            else:
                addToPinned_Action = menu.addAction(icon_from_file("pin"), tr("Add to pinned"))
                addToPinned_Action.triggered.connect(lambda: self.onAddToPinned_Action(chat))

        return menu

    def onMarkAllReadAction(self, chat=None, unmark=False):
        chat_api = ChatApi.instance()
        server_connect_config = chat_api.server_connect_config
        if server_connect_config and chat and chat.chat_id != None:
            if not chat.last_message:
                return

            if unmark:
                chat_api.unmark_last_read(chat.chat_id)
            else:
                chat_api.mark_last_read(chat.chat_id, chat.last_message.mes_id)

    def onAddToPinned_Action(self, chat):
        self.change_pinned_chat(chat, 'add')

    def onDelFromPinned_Action(self, chat):
        self.change_pinned_chat(chat, 'remove')

    def change_pinned_chat(self, chat, method_name):
        chat_api = ChatApi.instance()
        server_connect_config = chat_api.server_connect_config
        if server_connect_config and chat:
            pinned = 1 if method_name == 'add' else 0
            server_connect_config.set_pinned_chat(chat.chat_id, pinned)
            self.main_widget.updateBadges()

    def onMuteAction(self, mute_name, chat_id=None):
        chat_api = ChatApi.instance()
        server_connect_config = chat_api.server_connect_config
        if server_connect_config and chat_id != None:
            muted = 1 if mute_name == 'mute' else 0
            server_connect_config.set_muted_chat(chat_id, muted)
            self.main_widget.updateBadges()

    def onProfileAction(self, user_id, live_chat_id=None):
        self.main_widget.showProfile(user_id, live_chat_id=live_chat_id)

    def onDisconnectUserAction(self, user_id):
        ChatApi.instance().send(url='/user/disconnect/', attrs={'user_id':user_id})

    def onChatEdit(self, chat):
        self.main_widget.showChatEditDialog(chat)

    def onRemoveEdit(self, chat):
        ChatApi.instance().removeMeFromGroupChat(chat.chat_id)

    def onCreateGroupAction(self):
        dialog = ChatEditDialog(self.main_widget)
        dialog.exec()

    def onTakeLiveChat(self, chat):
        ChatApi.instance().take_live_chat(chat.chat_id)

    def onFinishLiveChat(self, chat):
        ChatApi.instance().finished_live_chat(chat.chat_id)

    def onCreateCoChat(self, chat):
        ChatApi.instance().create_cochat(chat.chat_id)

    def onOpenCoChat(self, chat):
        chat_id = chat.chat_id

        cochat_chat = ChatApi.instance().getChatById(chat.cochat)
        if cochat_chat:
            self.main_widget.showChatWithOpen(chat.cochat)
        else:
            ChatApi.instance().open_cochat(chat.chat_id)

    def onUpdateAction(self):
        chatApi = ChatApi.instance()
        chatApi.disconnect()
        chatApi.last_check_profiles = None
        chatApi.connect()

