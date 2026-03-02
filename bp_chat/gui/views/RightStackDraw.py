
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel

from ..core.draw import change_widget_background_color, change_widget_text_color, change_widget_font


class RightWidgetDraw(QLabel):

    rightStackWidget = None
    __mem_resizeEvent = None

    def __init__(self, rightStackWidget):
        super().__init__(rightStackWidget)
        self.setText("------- !!! Hi !!! -------")
        self.__mem_resizeEvent = rightStackWidget.resizeEvent
        self.rightStackWidget = rightStackWidget
        self.rightStackWidget.resizeEvent = self.__rightWidget_resizeEvent
        self.move(0, 46)

        change_widget_background_color(self, QColor(100, 100, 100))
        change_widget_text_color(self, QColor(255, 255, 255))
        change_widget_font(self, font_size=10, bold=True)

        self.setAlignment(Qt.AlignCenter)

    def __rightWidget_resizeEvent(self, event):
        ret = self.__mem_resizeEvent(event)

        size = self.rightStackWidget.size()
        self.resize(size.width(), 20)

        return ret
