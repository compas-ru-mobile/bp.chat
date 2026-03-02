#
# from PyQt5.QtWidgets import QListView, QAbstractItemView
# from PyQt5.QtCore import Qt, pyqtSignal
#
# from threading import Timer
# from sys import platform
#
# # border-right: 1px solid #cccccc;
#
# V_SCROLL_HIDE = """
# QScrollBar:vertical {
#     border: none;
#     background: rgba(255,255,255,255);
#     width: 0px;
#     margin: 0px 0px 0px 0px;
# }
# QScrollBar::handle:vertical {
#     background: rgba(255,255,255,255);
#     min-height: 20px;
# }
# QScrollBar::add-line:vertical {
#     background: rgba(0,0,0,0);
#     height: 0px;
#     subcontrol-position: bottom;
#     subcontrol-origin: margin;
# }
# QScrollBar::sub-line:vertical {
#     background: rgba(0,0,0,0);
#     height: 0px;
#     subcontrol-position: top;
#     subcontrol-origin: margin;
# }
# """
#
# V_SCROLL_SHOW = """
# QScrollBar:vertical {
#     border: none;
#     background: transparent;
#     width: 11px;
#     margin: 0px 1px 0px 0px;
# }
# QScrollBar::handle:vertical {
#     background: rgba(140,95,56,255);
#     margin: 2px 2px 2px 2px;
#     min-height: 20px;
#     border-radius: 3px;
# }
# QScrollBar::add-line:vertical {
#     background: rgba(0,0,0,0);
#     height: 0px;
#     subcontrol-position: bottom;
#     subcontrol-origin: margin;
# }
# QScrollBar::sub-line:vertical {
#     background: rgba(0,0,0,0);
#     height: 0px;
#     subcontrol-position: top;
#     subcontrol-origin: margin;
# }
# """
#
# class ListViewBase(QListView):
#
#     hideScrollSignal = pyqtSignal()
#
#     WIDTH_ADD_D = 0 if platform=='darwin' else 11
#
#     _width_add = 0
#     _scroll_visible = False
#     _need_show_case_mouse_pos = False
#     _try_hide_scroll_timer: Timer = None
#
#     def __init__(self, parent):
#         super().__init__(parent)
#         self.setMouseTracking(True)
#         self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
#         #self.verticalScrollBar().setSingleStep(15)
#         self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#         self.hideScrollSignal.connect(self.hideScroll)
#
#     @property
#     def width_add(self):
#         return self._width_add if self.verticalScrollBar() and self.verticalScrollBar().isVisible() else 0
#
#     def initAtStart(self):
#         self.setAttribute(Qt.WA_Hover, True)
#         self.hideScroll()
#
#     def hideScroll(self):
#         self._scroll_visible = False
#         self._width_add = 0
#         self.setStyleSheet(V_SCROLL_HIDE)
#
#     def showScroll(self):
#         self._scroll_visible = True
#         self._width_add = self.WIDTH_ADD_D
#         self.setStyleSheet(V_SCROLL_SHOW)
#
#     def enterEvent(self, *args, **kwargs):
#         #self.showScroll()
#         return super().enterEvent(*args, **kwargs)
#
#     def leaveEvent(self, *args, **kwargs):
#         self.hideScroll()
#         return super().leaveEvent(*args, **kwargs)
#
#     def mouseMoveEvent(self, event):
#         x = event.pos().x()
#         need_show = x >= self.width() * 0.8
#         self._need_show_case_mouse_pos = need_show
#         if self._scroll_visible != need_show:
#             if need_show:
#                 self.showScroll()
#             else:
#                 self.hideScroll() #self.startTryHideScroll(once=True)
#
#     def wheelEvent(self, event):
#         super().wheelEvent(event)
#         self.showScroll()
#         self.startTryHideScroll()
#
#     def startTryHideScroll(self, once=False):
#         if self._try_hide_scroll_timer and not once:
#             self._try_hide_scroll_timer.cancel()
#         self._try_hide_scroll_timer = Timer(0.5, self.tryHideScroll)
#         self._try_hide_scroll_timer.start()
#
#     def tryHideScroll(self):
#         if not self._need_show_case_mouse_pos:
#             self.hideScrollSignal.emit()
