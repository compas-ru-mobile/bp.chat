
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.Qt import Qt

from .ui.UiInputCallWidget import Ui_InputCallWidget

from bp_chat.logic.chat_api.ChatApi import ChatApi


class InputCallWidget(QWidget, Ui_InputCallWidget):

    from_text = None

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowFlags(#Qt.FramelessWindowHint |
                            Qt.WindowStaysOnTopHint)

        self.setupUi(self)
        self.retranslateUi(self)
        self.connectSignals()

    def fill(self, text):
        self.from_text = text
        self.fromLabel.setText(text)

    def connectSignals(self):
        self.openClientButton.clicked.connect(self.sendOpenClient)

    def sendOpenClient(self):
        if not self.from_text:
            return

        lst = self.from_text.split(':')
        if len(lst) > 1:
            reg_no = lst[1]

            ChatApi.instance().sendApi(compas={
                'type': 'app/signal',
                'dst': 'masters,crm',
                'signal/type': 'form/open',
                'form/open': {
                    'form': 'client',
                    'REG_NO': reg_no
                }
            })

