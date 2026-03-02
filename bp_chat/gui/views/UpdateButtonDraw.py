
from PyQt5.QtWidgets import QPushButton, QMessageBox
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import pyqtSignal, QObject

from time import sleep
from threading import Timer

from ...logic.chat_api import ChatApi
from ...logic.chat_api.ChatApiCommon import in_thread


class UpdateButtonDraw(QObject):

    button = None
    _progress = 0
    newProgress = pyqtSignal(int)
    _asked = pyqtSignal()
    _asked_timer = None
    __now_asking = False
    __showed = False

    def __init__(self, button):
        super().__init__(button)

        button.paintEvent = self.__allButtonPaintEvent
        self.button = button
        self.button.setProgress = self.setProgress
        self.button.showEvent = self.__buttonShowEvent

        self.newProgress.connect(self.onNewProgressSlot)
        self._asked.connect(self._onAskedSlot)

    def setProgress(self, progress):
        self.newProgress.emit(progress)

    def onNewProgressSlot(self, progress):
        self._progress = progress
        self.button.repaint()
        if progress == 100 and not self.__now_asking:
            self.__now_asking = True
            self.start_answer()

    @in_thread
    def start_answer(self):
        while not self.__showed:
            sleep(0.3)
        if self._asked_timer:
            self._asked_timer.cancel()
        self._asked_timer = Timer(0.3, self._asked_start)
        self._asked_timer.start()

    def _asked_start(self):
        self._asked.emit()

    def _onAskedSlot(self):
        ret = QMessageBox.question(self.button, "Update downloaded", "You can be updated. Do you want to restart application now?", QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            chatApi = ChatApi.ChatApi.instance()
            chatApi.startUpdate()
            chatApi.close_app_now()
        else:
            pass
        self.__now_asking = False

    def __allButtonPaintEvent(self, event, *args):
        ret = QPushButton.paintEvent(self.button, event, *args)

        painter = QPainter(self.button)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._progress > 0:
            h = self.button.height()
            w = int((self.button.width() * self._progress)/100)
            painter.fillRect(0, h-5, w, 2, QColor(70, 70, 70))

        painter.end()
        return ret

    def __buttonShowEvent(self, e):
        self.__showed = True
