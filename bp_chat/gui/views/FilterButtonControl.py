
from PyQt5.QtWidgets import QWidget, QItemDelegate, QToolButton, QHBoxLayout
from PyQt5.QtCore import Qt, QSize, QPointF
from PyQt5.QtGui import QColor, QIcon, QPainter

from ..core.draw import draw_badges, draw_pixmap_file, draw_text
from ...logic.chat_api import ChatApi
from bp_chat.gui.common.langs import tr


class FilterButtonsControl:

    selected = None
    find_text = ""
    chats = None
    badges_count_all = 0
    badges_count_all_muted = 0
    filter_starter = None

    def __init__(self, allButton, groupsButton, contactsButton, liveButton, main_widget):
        self.main_widget = main_widget
        self.filters = []
        self.selected = FilterAll(allButton if allButton!=True else None, filterControl=self)
        if groupsButton:
            FilterGroups(groupsButton, filterControl=self)
        if contactsButton:
            FilterContacts(contactsButton, filterControl=self)
        if liveButton:
            FilterLive(liveButton, filterControl=self)

    def set_filter_starter(self, filter_starter):
        self.filter_starter = filter_starter

    def filter(self):
        chat_api = ChatApi.ChatApi.instance()
        self.chats = chat_api.chats

        if self.chats == None:
            self.chats = []

        badges = 0
        mutes = 0
        if self.chats:
            for chat in self.chats:
                badges_count = chat.get_badges_count()
                badges += badges_count
                if chat.is_chat_muted():
                    mutes += badges_count

        self.badges_count_all = badges
        self.badges_count_all_muted = mutes

        for fi in self.filters:
            fi.filter()
            if fi == self.selected:
                self.chats = fi.chats

    def sort(self, chats, key=lambda ch, ret: ret):
        server_connect_config = ChatApi.ChatApi.instance().server_connect_config
        pinned = []
        if server_connect_config:
            pinned = server_connect_config.get_pinned_chats()
        return sorted(chats, key=lambda ch:key(ch, (
            ch.chat_id not in pinned,
            -ch.get_badges_state(), #(0 if ch.get_badges_count() > 0 else 1),
            -ch.last_message_time_to_long(),
            ch.getName()
        )))

    def updateButtons(self):
        self.filter_starter()
        for fi in self.filters:
            fi.button.update()
        if self.main_widget:
            self.main_widget.updateChatsListView(source='FilterButtonsControl.updateButtons')

    def setFindText(self, text):
        #self.main_widget.listView.clear_selection()
        self.find_text = text
        if self.filter_starter:
            self.filter_starter()
        if self.main_widget:
            self.main_widget.updateChatsListView(source='FilterButtonsControl.setFindText')

    def setAllBadgesCount(self, badgesCount):
        if self.badges_count_all != badgesCount:
            self.filter_starter()
            self.badges_count_all = badgesCount
            return True
        return False

    def get_chats(self):
        return self.chats


class FilterButtonControl:

    button = None
    chats = None
    title = None
    icon_name = None

    def __init__(self, button, filterControl):
        if button:
            button.paintEvent = self.__allButtonPaintEvent
            self.button = button
            self.button.filter_control = self
            self.button.clicked.connect(self.onClick)
        self.filterControl = filterControl
        self.filterControl.filters.append(self)

    def __allButtonPaintEvent(self, event, *args):
        ret = None
        #ret = QToolButton.paintEvent(self.button, event, *args)

        painter = QPainter(self.button)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.button.width(), self.button.height()

        draw_pixmap_file(painter, self.icon_name, w/2-18, h/2-36, 36, 36)

        draw_text(painter, tr(self.title), w/2, h/2+18, align='center', valign='center')

        if not self.is_selected():
            painter.fillRect(0, 0, self.button.width(), self.button.height(), QColor(255, 193, 7, 100))

        # draw badges
        badges, muted = self.count_badges()
        if badges > 0:
            is_muted = muted >= badges
            if muted > 0 and muted < badges:
                badges -= muted
            draw_badges(painter, badges, self.button.width() - 20, self.button.height() - 30, muted=is_muted)

        if self.is_selected():
            pen = painter.pen()
            pen.setWidth(2)
            pen.setColor(QColor(30, 30, 30))
            painter.setPen(pen)

            h = self.button.height() - 2
            painter.drawLine(0, h, self.button.width(), h)

        painter.end()

        return ret

    def is_selected(self):
        return self.filterControl.selected == self

    def onClick(self, *args):
        self.show()
        self.filterControl.selected = self
        self.filterControl.updateButtons()

    def count_badges(self):
        if self.chats == None:
            return 0
        muted = [0]
        chat_api = ChatApi.ChatApi.instance()
        return sum(self._upd_muted(chat, muted, chat_api) for chat in self.chats if chat.badges_count > 0), muted[0]

    def _upd_muted(self, chat, muted, chat_api):
        badges = chat.get_badges_count()
        if chat.is_chat_muted() and badges > 0:
            muted[0] += badges
        return badges

    def filter(self):
        chats = ChatApi.ChatApi.instance().chats

        if chats == None:
            chats = []

        chats = self.do_filter(chats)
        text = self.filterControl.find_text.strip().lower()
        if len(text) != 0:
            chats = [chat for chat in chats if text in chat.getName().lower() or text in chat.getLogin().lower()]

        self.chats = self.sort(chats)

    def do_filter(self, chats):
        raise NotImplementedError

    def show(self):
        if self.filterControl.main_widget:
            self.filterControl.main_widget.onlyOnlineWidget.show()

    def sort(self, chats):
        return self.filterControl.sort(chats)


class FilterAll(FilterButtonControl):
    title = 'ALL'
    icon_name = 'all'

    def show(self):
        if self.filterControl.main_widget:
            self.filterControl.main_widget.onlyOnlineWidget.hide()

    def do_filter(self, chats):
        return [ chat for chat in chats if not chat.is_live() ]


class FilterGroups(FilterButtonControl):
    title = 'GROUPS'
    icon_name = 'group_black'

    def show(self):
        if self.filterControl.main_widget:
            self.filterControl.main_widget.onlyOnlineWidget.hide()

    def do_filter(self, chats):
        return [ chat for chat in chats if chat.is_group() ]


class FilterContacts(FilterButtonControl):
    title = 'CONTACTS'
    icon_name = 'profile'

    def do_filter(self, chats):
        if self.filterControl.main_widget:
            only_online = self.filterControl.main_widget.onlyOnlineCheckBox.isChecked()
        else:
            only_online = False
        chats = [ chat for chat in chats if chat.is_private() ]
        if only_online:
            chats = [chat for chat in chats if chat.user.is_online()]
        return chats

    def sort(self, chats):
        server_connect_config = ChatApi.ChatApi.instance().server_connect_config
        pinned = []
        if server_connect_config:
            pinned = server_connect_config.get_pinned_chats()
        key=lambda ch, ret: ret
        if self.filterControl.main_widget:
            only_online = self.filterControl.main_widget.onlyOnlineCheckBox.isChecked()
        else:
            only_online = False
        if only_online:
            return sorted(chats, key=lambda ch:key(ch, (
                ch.chat_id not in pinned,
                -ch.get_badges_state(), #(0 if ch.get_badges_count() > 0 else 1),
                ch.user.status,
                -ch.last_message_time_to_long(),
                ch.getName()
            )))
        return sorted(chats, key=lambda ch:key(ch, (
            ch.chat_id not in pinned,
            -ch.get_badges_state(), #(0 if ch.get_badges_count() > 0 else 1),
            -ch.last_message_time_to_long(),
            ch.getName()
        )))


        if self.filterControl.main_widget:
            only_online = self.filterControl.main_widget.onlyOnlineCheckBox.isChecked()
        else:
            only_online = False
        if only_online:
            sorter = lambda ch, ret: ((0 if ch.get_badges_count() > 0 else 1), ch.user.status, ch.getName())
        else:
            sorter = lambda ch, ret: ((0 if ch.get_badges_count() > 0 else 1), ch.getName())
        return self.filterControl.sort(chats, key=sorter)


class FilterLive(FilterButtonControl):
    title = 'LIVE'
    icon_name = 'live'

    def show(self):
        if self.filterControl.main_widget:
            self.filterControl.main_widget.onlyOnlineWidget.hide()

    def do_filter(self, chats):
        return [ chat for chat in chats if chat.is_live() ]

    def sort(self, chats):
        return self.filterControl.sort(chats, key=lambda ch, ret: (
            ret[0],
            -ch.get_live_state(),
            ret[1],
            *ret[2:]
        ))