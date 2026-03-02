from os.path import exists, join

from PyQt5.QtWidgets import QListView, QMenu, QAbstractItemView
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtCore import Qt, QModelIndex, QItemSelectionModel, QItemSelection, QAbstractItemModel, QPoint, QRect

from ...logic.chat_api import ChatApiCommon
from ...logic.chat_api.ChatApi import ChatApi
from ...logic.datas.Message import Message
#from .ListViewBase import ListViewBase
from ..paint.Selection import Selection
from ..delegates.MessagesDictDelegate import MessagesDictDelegate
from ..models.list_model import MessagesListView as _MessagesListView


class MessagesListView(_MessagesListView):

    def clearSelectionText(self): # FIXME clearSelectionText
        pass
