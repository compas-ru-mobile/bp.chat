from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFontMetrics, QPalette

from bp_chat.logic.datas.Message import Message


def makeResendWidgetBase(self, resendMessage, displayResendWidget=True, custom_width=None):
    is_message = isinstance(resendMessage, Message)

    if displayResendWidget:
        self.displayResendWidget(is_message)

    if is_message:
        sender = resendMessage.getSenderName()
        text = resendMessage.text

        palette = self.resendSenderLabel.palette()
        palette.setColor(QPalette.WindowText, QColor('#ffc107'))
        self.resendSenderLabel.setPalette(palette)

        f = self.resendMessageLabel.font()
        fm = QFontMetrics(f)
        width = self.resendMessageLabel.width()

        elided_text = fm.elidedText(text, Qt.ElideRight, custom_width if custom_width else width)
        self.resendSenderLabel.setText(sender)
        self.resendMessageLabel.setText(elided_text)


# from os.path import abspath, join, dirname
#
# from PyQt5.QtGui import QColor, QPainter, QIcon, QFont, QPalette, QBitmap
# from PyQt5.QtCore import Qt, QSize, QPointF, QRect, QRectF, QPoint
#
# _IMGS_PREFFIX = ''
#
# def set_imgs_preffix(val):
#     global _IMGS_PREFFIX
#     _IMGS_PREFFIX = val
#
#
# def draw_badges(painter, badges, left, top, font_pixel_size=10, factor=1, muted=False):
#
#     # draw badges
#     pen = painter.pen()
#     pen.setWidth(1)
#     painter.setPen(pen)
#
#     badges = str(badges)
#
#     main_color = QColor(150, 150, 150) if muted else QColor(255, 100, 100)
#
#     painter.setPen(QColor(255, 100, 100, 0))
#     painter.setBrush(main_color)
#     painter.drawEllipse(QPointF(left + 6*factor, top - 3*factor), 8*factor, 8*factor)
#
#     if len(badges) > 1:
#         left_minus = (6*factor) * (len(badges)-1)
#         left -= left_minus
#         painter.drawEllipse(QPointF(left + 6*factor, top - 3*factor), 8*factor, 8*factor)
#         painter.fillRect(left+6*factor, top - (3 + 8)*factor, left_minus, (8*2)*factor, main_color)
#
#     painter.setPen(QColor(255, 255, 255))
#     #font = painter.font()
#     font = QFont("Arial")
#     font.setPixelSize(font_pixel_size)
#     #font.setPointSize(6)
#     font.setBold(True)
#     painter.setFont(font)
#     painter.drawText(left, top, "+{}".format(badges))
#
# def draw_dot(painter, left, top, factor=1, muted=False):
#     # pen = painter.pen()
#     # pen.setWidth(1)
#     # painter.setPen(pen)
#
#     main_color = QColor(150, 150, 150) if muted else QColor(255, 100, 100)
#     secon_color = QColor(50, 50, 50) if muted else QColor(150, 50, 50)
#
#     painter.setPen(secon_color)
#     pen = painter.pen()
#     pen.setWidth(factor*3)
#     painter.setPen(pen)
#
#     painter.setBrush(main_color) #255, 100, 100))
#     painter.drawEllipse(QPointF(left + 6 * factor, top - 3 * factor), 8 * factor, 8 * factor)
#
#     # painter.setPen(QColor(255, 255, 255))
#     # # font = painter.font()
#     # font = QFont("Arial")
#     # font.setPixelSize(font_pixel_size)
#     # # font.setPointSize(6)
#     # font.setBold(True)
#     # painter.setFont(font)
#
# def draw_text(painter, text, left, top, align='left', valign='bottom'):
#     r = painter.boundingRect(QRectF(0, 0, 9999, 9999), text)
#     w, h = r.width(), r.height()
#
#     if align == 'center':
#         left = left - w/2
#     if valign == 'center':
#         top = top - h/2
#
#     painter.drawText(left, top, text)
#
#
# def draw_pixmap_file(painter, icon_name, left, top, width, height):
#     pixmap = pixmap_from_file(icon_name, width, height)
#     if pixmap:
#         painter.drawImage(QPointF(left, top), pixmap.toImage())
#
#
# def pixmap_from_file(icon_name, to_width, to_height):
#     icon = icon_from_file(icon_name)
#     return icon.pixmap(QSize(to_width, to_height))
#
# def pixmap_from_icon(icon, to_width, to_height):
#     return icon.pixmap(QSize(to_width, to_height))
#
# def icon_from_file(icon_name):
#     return QIcon(path_to_images() + "/" +
#                  icon_name + ".png")
#
# def path_to_images():
#     return ':/images/data/images/'
#     #return abspath(join(dirname(abspath(__file__)), _IMGS_PREFFIX + '../../../data/images/'))
#
#
# def draw_badges_on_icon(icon, badges, only_dot=False, muted=False):
#     if badges <= 0:
#         return icon
#     pix = icon.pixmap(QSize(150, 150))
#     painter = QPainter(pix)
#     if only_dot:
#         draw_dot(painter, left=10, top=35, factor=3, muted=muted)
#     else:
#         draw_badges(painter, badges, left=50, top=70, font_pixel_size=64, factor=7, muted=muted)
#     painter.end()
#     icon = QIcon(pix)
#     return icon
#
#
# def change_widget_background_color(widget, color):
#     palette = widget.palette()
#     palette.setColor(widget.backgroundRole(), color)
#     widget.setPalette(palette)
#     widget.setAutoFillBackground(True)
#     return palette
#
# def change_widget_text_color(widget, color):
#     palette = widget.palette()
#     palette.setColor(QPalette.WindowText, color)
#     widget.setPalette(palette)
#     return palette
#
# def change_widget_font(widget, font_size, font_family="Arial", bold=False):
#     font = widget.font()
#     font.setPointSize(font_size)
#     font.setBold(bold)
#     font.setFamily(font_family)
#     widget.setFont(font)
#     return font
#
# def color_from_hex(hex_color):
#     hex_color = hex_color.replace("#", "")
#
#     # lst = [ hex_color[i * 2:i * 2 + 2] for i in range(3)]
#     # raise Exception(str(lst))
#
#     lst = [ int(hex_color[i*2:i*2+2], 16) for i in range(3) ]
#
#     return QColor(*lst)
#
#
# def pixmap_from_icon_rounded(icon, to_size=(50, 50), mask_func=None, border_radius=None):
#     availableSizes = icon.availableSizes()
#     if len(availableSizes) == 0:
#         return None
#
#     sz = availableSizes[0]
#     sz_w, sz_h = sz.width(), sz.height()
#     _w, _h = to_size
#
#     if sz_w != sz_h:
#         if sz_w > sz_h:
#             _w = int(round(float(_w) * sz_w / sz_h))
#         else:
#             _h = int(round(float(_h) * sz_h / sz_w))
#
#     pixmap = pixmap_from_icon(icon, _w*5, _h*5)
#     sz = pixmap.size()
#     _w2, _h2 = sz.width(), sz.height()
#     if _w2 > _h2:
#         _image_left_add = - int((_w2 - _h2) / 2)
#
#     to_5 = (min(_w2, _h2), min(_w2, _h2))
#     _factor = int(round(float(to_5[0]) / 50.0))
#     if border_radius:
#         border_radius *= _factor
#     if mask_func:
#         pixmap.setMask(mask_func(size=(_w2, _h2), to_size=(to_size[0]*5,to_size[1]*5)))
#     else:
#         pixmap.setMask(get_round_mask(size=(_w2, _h2), to_size=to_5, border_radius=border_radius))
#
#     pixmap = pixmap.scaled(QSize(_w, _h), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
#
#     return pixmap
#
#
# def get_round_mask(size=(50, 50), to_size=(50, 50), border_radius=None):
#     _w, _h = size
#     w, h = to_size
#
#     map = QBitmap(_w, _h)
#
#     painter = QPainter(map)
#     painter.setRenderHint(QPainter.Antialiasing)
#
#     painter.setPen(QColor(0, 0, 0))
#     painter.setBrush(QColor(0, 0, 0))
#
#     left = 0
#     if _w > _h:
#         left = int((_w - _h) / 2)
#
#     rect = QRect(left, 0, w, h)
#     full_rect = QRect(0, 0, _w, _h)
#     painter.fillRect(full_rect, QColor(255, 255, 255))
#
#     if border_radius:
#         br = border_radius
#         #full_rect = QRect(br, br, _w - br * 2, _h - br * 2)
#         for i in ((br, 0, _w-br*2, _h), (0, br, _w, _h-br*2)):
#             painter.fillRect(QRect(*i), QColor(0, 0, 0))
#
#         for x, y in ((br, br), (_w-br, br), (_w-br, _h-br), (br, _h-br)):
#             painter.drawEllipse(QPoint(x, y), br, br)
#     else:
#         painter.drawEllipse(rect)
#
#     painter.end()
#
#     return map
