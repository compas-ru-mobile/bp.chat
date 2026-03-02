
from PyQt5.QtWidgets import QItemDelegate
from PyQt5.QtGui import QColor, QPainter, QIcon
from PyQt5.QtCore import QSize, QAbstractListModel, QPointF, Qt, QRectF, QRect, QPoint, QItemSelectionModel, pyqtSignal

from ...logic.chat_api.ChatApi import ChatApi
from ..core.draw import pixmap_from_icon_rounded, icon_from_file

from threading import Timer

#from ..views.ListViewBase import V_SCROLL_HIDE, V_SCROLL_SHOW


class UsersDictDelegate(QItemDelegate):

    def __init__(self, listView, filter_text='', only_checked=False):
        self.listView = listView
        self.only_checked = only_checked
        # self.listView.setAttribute(Qt.WA_Hover, True)
        # self.listView.enterEvent = self.enterEvent
        # self.listView.leaveEvent = self.leaveEvent
        # self.listView.showEvent = self.showEvent
        self.filter_text = filter_text
        super().__init__(listView)

    def paint(self, painter, option, index):

        if option.rect.height() <= 0:
            return

        left, top, right, bottom = option.rect.left(), option.rect.top(), option.rect.right(), option.rect.bottom()

        painter.setRenderHint(QPainter.Antialiasing)

        background_color = QColor(255, 255, 255)

        # if option.showDecorationSelected:
        #     background_color = QColor(255, 255, 150)

        inds = self.listView.selectedIndexes()
        checked = Qt.Unchecked
        for ind in inds:
            if ind.row() == index.row():
                checked = Qt.Checked

        painter.fillRect(option.rect.adjusted(1, 0, 0, 0), background_color)  # Qt.SolidPattern)

        users = self.get_users()
        user = users[index.row()]

        painter.setPen(QColor('#e7e6bc'))
        painter.setBrush(QColor('#e7e6bc'))
        painter.drawEllipse(QPointF(left + 20 + 10, top + 20 + 10), 20, 20)

        up = user.profile
        btm = up.getBitmap()
        offset_x = offset_y = 0 # FIXME hack
        pixmap = None
        if btm:
            pixmap = pixmap_from_icon_rounded(btm, to_size=(40, 40))
            if pixmap:
                offset_x = (pixmap.width() - 40)/2
                offset_y = (pixmap.height() - 40)/2
        if not pixmap:
            icon = icon_from_file("user")
            pixmap = icon.pixmap(QSize(40, 40))
        painter.drawImage(QPointF((left + 10) - offset_x, (top + 10) - offset_y), pixmap.toImage())

        painter.setPen(QColor(30, 30, 30))
        painter.drawText(left + 40 + 20, top + 34, user.name)

        # checked = Qt.Checked
        # if sum(map(int, user.name.split(' ')[-1])) > 10:
        #     checked = Qt.Unchecked

        self.drawCheckDo(painter, option, QRect(right - (bottom - top), top, bottom - top, bottom - top), checked)

        painter.setPen(QColor(192, 192, 192))
        painter.drawLine(left+60, top+59, right, top+59)

    def drawCheckDo(self, painter, option, rect, checked):
        r = QRect(rect.left(), int(rect.top()+rect.height()/2-5), 10, 10)
        painter.drawRect(r)
        if checked:
            painter.setPen(QColor('#333333'))
            painter.setBrush(QColor('#333333'))
            painter.drawEllipse(QPointF(r.left()+5, r.top()+5), 3, 3)

    def sizeHint(self, option, index):
        if self.only_checked:
            inds = self.listView.selectedIndexes()
            checked = Qt.Unchecked
            for ind in inds:
                if ind.row() == index.row():
                    checked = Qt.Checked
                    break
            if not checked:
                return QSize(int(option.rect.right()), 0)
        return QSize(int(option.rect.right()), 60)

    def get_users(self):
        chat_api = ChatApi.instance()
        c_u_id = chat_api.getCurrentUserId()
        users = [u for u in chat_api.users.values() if int(u.id) != int(c_u_id)]
        return list(filter(self.filter, sorted(users, key=lambda u: u.name.lower())))

    def filter(self, user):
        return self.filter_text.lower() in user.name.lower()

    def set_filter_text(self, filter_text=""):
        self.filter_text = filter_text

    def set_only_checked(self, only_checked):
        self.only_checked = only_checked

    # def hideScroll(self):
    #     self.listView.setStyleSheet(V_SCROLL_HIDE)
    #
    # def showScroll(self):
    #     self.listView.setStyleSheet(V_SCROLL_SHOW)
    #
    # def enterEvent(self, *args, **kwargs):
    #     self.showScroll()
    #     #return super().enterEvent(*args, **kwargs)
    #
    # def leaveEvent(self, *args, **kwargs):
    #     self.hideScroll()
    #     #return super().leaveEvent(*args, **kwargs)
    #
    # def showEvent(self, *args, **kwargs):
    #     self.hideScroll()

    def on_mouse_pos_changed(self, *args, **kwargs):
        pass


class UsersDictModel(QAbstractListModel):

    updateMeSignal = pyqtSignal()
    updateMeTimer = None

    def __init__(self, delegate):
        super().__init__()
        self.delegate = delegate
        self.updateMeSignal.connect(self.updateMeSlot)

    def rowCount(self, parent=None):
        return len(self.delegate.get_users())

    def data(self, index, role=None):
        users = self.delegate.get_users()
        return users[index.row()]

    def updateMe(self, clear=False, filter_text="", only_checked=False):
        self.delegate.set_filter_text(filter_text)
        self.delegate.set_only_checked(only_checked)
        if self.updateMeTimer:
            self.updateMeTimer.cancel()
        self.updateMeTimer = Timer(0.1, self.updateMeStart)
        self.updateMeTimer.start()

    def update_items(self):
        self.updateMe()

    def updateMeStart(self):
        self.updateMeSignal.emit()

    def updateMeSlot(self):
        count = self.rowCount()
        self.beginResetModel()
        self.endResetModel()
        self.delegate.listView.refresh_checked() # FIXME