
from threading import Timer
from PyQt5.QtGui import QHoverEvent
from PyQt5.QtWidgets import QListView, QMenu
from PyQt5.QtCore import Qt, pyqtSignal

from ..ChatEditDialog import ChatEditDialog
from ...logic.chat_api.ChatApi import ChatApi
#from ..delegates.MessagesDictDelegate import MessagesDictModel, MessagesDictDelegate
from ..core.draw import icon_from_file

from ..models.list_model import ChatsListView as _ChatsListView


class ChatsListView(_ChatsListView):

    def clear_selection(self):
        ChatApi.instance().setCurrentChatId(-1)
        super().clear_selection()

