
from os.path import exists
from contextlib import contextmanager

from PyQt5.QtGui import QPainter, QIcon, QPen, QColor, QFont, QFontMetrics
from PyQt5.QtCore import QSize, QPointF, QRect, QPoint, Qt

from bp_chat.logic.chat_api import ChatApiCommon
from bp_chat.logic.chat_api.ChatApi import ChatApi
from bp_chat.logic.datas.QuoteInfo import QuoteInfo
from bp_chat.logic.datas.Message import Message
from ..core.draw import icon_from_file
from .Word import WORD_TYPE_LINK
from bp_chat.gui import paint
from bp_chat.logic.chat_api.ChatApiCommon import SMILES

LINE_TYPE_BASE = -1
LINE_TYPE_FILE = 100



class LineBase:
    line_type = LINE_TYPE_BASE


class HeaderLine(LineBase):

    def __init__(self, message:Message, mes_drawer: 'paint.MessageDrawer'):
        self.message = message
        self.mes_drawer = mes_drawer

    def get_size(self, font_height):
        if self.mes_drawer.need_show_sender_name:
            return (0, font_height)
        else:
            return (0, 0)

    def draw(self, painter: QPainter, text_rect, font_height, mouse_pos):
        if self.mes_drawer.need_show_sender_name:
            with change_font(painter, bold=True, simple_font=True):
                painter.drawText(text_rect.left(), text_rect.top()+font_height, self.message.getSenderName())


class FooterLine(LineBase):

    padding_x = 10
    padding_y = 0

    def __init__(self, message:Message, mes_drawer: 'paint.MessageDrawer'):
        self.message = message
        self.mes_drawer = mes_drawer

    def get_size(self, font_height):
        return (0, font_height)

    def draw(self, painter: QPainter, text_rect, font_height, mouse_pos):
        with change_font(painter, simple_font=True, bold=False, font_size=12, text_color=self.mes_drawer.delegate.INFO_COLOR):
            #painter.drawText(text_rect.left(), text_rect.top()+font_height, self.message.getSenderName())
            self._draw_right_text(painter, self.message, (text_rect.left(), text_rect.top(), text_rect.right(), text_rect.bottom()))

    def _draw_right_text(self, painter, message, left_top_right_bottom):
        left, top, right, bottom = left_top_right_bottom

        # right bottom text with date and delivered
        # painter.setPen(QColor(self.mes_drawer.delegate.INFO_COLOR))
        # font = self.mes_drawer.delegate.simple_font
        # font.setBold(False)
        # font.setPixelSize(12)
        # painter.setFont(font)
        font = painter.font()
        font_h = QFontMetrics(font).height()

        delivered_icon = self.mes_drawer.delegate.get_delivered_icon(message)

        # render icon delivered
        if delivered_icon is not None:
            avatar_pixmap = delivered_icon.pixmap(QSize(int(QFontMetrics(font).height()), int(QFontMetrics(font).height())))
            painter.drawImage(QPointF(right - (QFontMetrics(font).height() + self.padding_x), #+ self.listView.width_add,
                                      bottom - font_h - self.padding_y), avatar_pixmap.toImage())  # FIXME 5...

        date_text = "{}".format(message.getTimeString())
        date_text_width = QFontMetrics(font).width(date_text)


        _top_left = QPoint(
            int(right - (date_text_width + self.padding_x + 5 + QFontMetrics(font).height())), #+ self.listView.width_add,
            int(bottom - font_h - self.padding_y)
        )
        dateTextRect = QRect(_top_left, QSize(int(date_text_width), int(QFontMetrics(font).height())))

        painter.drawText(dateTextRect, Qt.AlignLeft, date_text)

        # painter.drawLine(left, bottom - font_h - self.padding_y, right, bottom - font_h - self.padding_y)
        # painter.drawLine(left, bottom, right, bottom)

        return font_h


class WordsLine(LineBase, list):

    def __init__(self, lst):
        list.__init__(self, lst)

    def get_size(self, font_height):
        return (0, font_height)

    def draw_line(self, mes_drawer, painter: QPainter, delegate,
                  message, word_num: int, x: int, y: int, y_start: int,
                  mouse_pos, selection, selection_sorted,
                  font_width, letter_width: float, temp_pen, last_w_drawn):
        for w in self:
            word_num += 1
            x_end = x + len(w) * letter_width

            pen_changed = False
            if w.word_type == WORD_TYPE_LINK:
                pen_changed = True
                if y_start <= mouse_pos[1] < y and x <= mouse_pos[0] <= x_end:
                    painter.setPen(QPen(QColor(delegate.LINK_COLOR_HOVER)))
                    painter.drawLine(x, y + 3, x_end, y + 3)
                    delegate.listView.cursor_need_cross = True
                else:
                    painter.setPen(QPen(QColor(delegate.LINK_COLOR)))
                rect = (x, y_start, x_end, y)
                mes_drawer.links.add((w, rect))

            word_start = word_end = xx_end = None
            if selection:
                is_word_in_selection = selection.is_word_in_selection(
                    message.mes_id, word_num,
                    QRect(QPoint(x, y_start), QPoint(x_end, y)),
                    selection_sorted, mes_drawer
                )
                if is_word_in_selection:
                    x_minus = font_width if last_w_drawn else 0
                    xx = x
                    xx_end = x_end
                    if type(is_word_in_selection) == tuple:
                        _, word_start, word_end = is_word_in_selection
                        if word_start is not None and word_start > 0:
                            xx += word_start * letter_width
                            x_minus = 0
                        if word_end is not None and word_end < len(w):
                            xx_end = x + word_end * letter_width

                    pen_changed = True
                    painter.setPen(QColor(delegate.TEXT_WHITE_COLOR))
                    painter.fillRect(QRect(QPoint(xx - x_minus, y_start + 3),
                                           QPoint(xx_end, y + 3)), QColor(delegate.LINK_COLOR))
                    last_w_drawn = True

            for sm in SMILES:
                w = w.replace(sm, "?")

            painter.drawText(x, y, w)

            if pen_changed:
                painter.setPen(temp_pen)
                if word_start is not None and word_start > 0:
                    painter.drawText(x, y, w[:word_start])
                if word_end is not None and word_end < len(w):
                    painter.drawText(xx_end, y, w[word_end:])

            x = x_end + letter_width

        return word_num, x, last_w_drawn

    def get_selected_line(self, message, word_num, x, y, y_start, letter_width, selection, selection_sorted):
        new_line = []
        for w in self:
            word_num += 1
            x_end = x + len(w) * letter_width

            if selection:
                is_word_in_selection = selection.is_word_in_selection(
                    message.mes_id, word_num,
                    QRect(QPoint(x, y_start), QPoint(x_end, y)),
                    selection_sorted, self
                )
                if is_word_in_selection:
                    text = w
                    word_start = 0
                    word_end = len(w)
                    if type(is_word_in_selection) == tuple:
                        _, word_start, word_end = is_word_in_selection
                        if word_start is None:
                            word_start = 0
                        if word_end is None:
                            word_end = len(w)

                    text = text[word_start:word_end]
                    new_line.append(text)

        return new_line, word_num

    def find_selection_start_word_pos(self, xxx, yyy, x, y_start, word_num, letter_width):
        for w in self:
            word_num += 1
            x_end = x + len(w) * letter_width

            if y_start > yyy:
                return word_num, 0

            elif yyy-16 < y_start <= yyy and xxx <= x_end:
                word_start = 0
                d = xxx - x
                if d > 0:
                    word_start = int(d / letter_width)
                return word_num, word_start

            x = x_end + letter_width

        return word_num, None

    def find_selection_end_word_pos(self, xxx, yyy, x, y_start, word_num, letter_width, word_end):
        for w in self:
            word_num += 1
            x_end = x + len(w) * letter_width
            _word_end = len(w)

            if y_start > yyy:
                return True, word_num - 1, word_end

            elif yyy - 16 < y_start <= yyy and xxx <= x_end + letter_width:
                d = xxx - x
                word_end = _word_end
                if d > 0:
                    word_end = int(d / letter_width)
                return True, word_num, word_end

            x = x_end + letter_width
            word_end = _word_end

        return False, word_num, word_end


class QuoteAuthor(LineBase):

    # first_word_left = 10
    # line_height = 8
    margin_first_top = 4

    def __init__(self, quote: QuoteInfo, message_drawer):
        self.quote = quote
        self.message_drawer = message_drawer

    @property
    def first_word_left(self):
        sender = self.quote.getSenderName()
        if not sender or len(sender) == 0:
            return 0
        return 10

    @property
    def line_height(self):
        sender = self.quote.getSenderName()
        if not sender or len(sender) == 0:
            return 0
        return 8

    def get_size(self, font_height):
        sender = self.quote.getSenderName()
        if not sender or len(sender) == 0:
            return 0, 0
        return 0, font_height

    def draw(self, painter: QPainter, text_rect, font_height, mouse_pos):

        temp_pen = painter.pen()
        temp_font = painter.font()

        painter.setPen(QPen(QColor(self.message_drawer.delegate.RESEND_COLOR)))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        fm = QFontMetrics(font)
        font_h = fm.height()

        painter.drawText(text_rect.left(), text_rect.top()+font_height, self.quote.getSenderName())

        painter.setPen(temp_pen)
        painter.setFont(temp_font)


class QuoteLine(WordsLine):

    first_word_left = 10
    line_height = 14
    # padding_first_top = 10
    margin_last_bottom = 10

    def __init__(self, lst, quote: QuoteInfo):
        self.quote = quote
        super().__init__(lst)

    def draw_line(self, mes_drawer, painter: QPainter, delegate,
                  message, word_num: int, x: int, y: int, y_start: int,
                  mouse_pos, selection, selection_sorted,
                  font_width, letter_width: float, temp_pen, last_w_drawn):
        pen = QPen(QColor(mes_drawer.delegate.INFO_COLOR))
        painter.setPen(pen)
        word_num, x, last_w_drawn = super().draw_line(mes_drawer, painter, delegate,
                  message, word_num, x, y, y_start,
                  mouse_pos, selection, selection_sorted,
                  font_width, letter_width, pen, last_w_drawn)
        painter.setPen(temp_pen)
        return word_num, x, last_w_drawn


class FileLine(LineBase):

    # first_word_left = 5

    line_type = LINE_TYPE_FILE

    def __init__(self, file_uuid, filename, filesize, message_drawer):
        self.file_uuid = file_uuid
        self.filename = filename
        self.filesize = filesize
        self.message_drawer = message_drawer

    def get_size(self, font_height):
        _fullpath = ChatApiCommon.getDownloadsFilePath(self.filename, self.file_uuid)
        file_exists = exists(_fullpath)

        pixmap_w, pixmap_h = 30, 30

        if file_exists:
            _lower_fullpath = _fullpath.lower()
            if _lower_fullpath.endswith('.jpg') or _lower_fullpath.endswith('.png'):

                icon = ChatApi.instance().images.get(self.file_uuid, None)
                if not icon:
                    icon = QIcon(_fullpath)
                    ChatApi.instance().images[self.file_uuid] = icon

                sizes = icon.availableSizes()
                if sizes and len(sizes) > 0:
                    # self.images[_file_uuid] = icon
                    sz = sizes[0]
                    _w, _h = sz.width(), sz.height()
                    if _h > 100:
                        _h = 100
                        dh = _h / 100.0
                        _w = int(round(_w / dh))

                    if _w > 200:
                        _w = 200
                        dw = _w / 200
                        _h = int(round(_h / dw))

                    isz = icon.actualSize(QSize(int(_w), int(_h)))
                    if isz.width() > 0 and isz.height() > 0:
                        pixmap_w, pixmap_h = isz.width(), isz.height()

        return pixmap_w, pixmap_h

    def draw(self, painter: QPainter, text_rect, font_height, mouse_pos):
        _fullpath = ChatApiCommon.getDownloadsFilePath(self.filename, self.file_uuid)
        file_exists = exists(_fullpath)

        pixmap_w, pixmap_h = self.get_size(font_height)

        if file_exists:
            _lower_fullpath = _fullpath.lower()
            if _lower_fullpath.endswith('.jpg') or _lower_fullpath.endswith('.png'):
                icon = QIcon(_fullpath)
                isz = icon.actualSize(QSize(int(pixmap_w), int(pixmap_h)))
                if isz.width() > 0 and isz.height() > 0:
                    pixmap_w, pixmap_h = isz.width(), isz.height()
                else:
                    icon = icon_from_file("file")
            else:
                icon = icon_from_file("file")

        else:
            icon = icon_from_file("download_file")

        file_pixmap = icon.pixmap(QSize(int(pixmap_w), int(pixmap_h)))
        self._draw_file(painter, file_pixmap, text_rect, pixmap_w, pixmap_h, mouse_pos)

    def _draw_file(self, painter, file_pixmap, text_rect, pixmap_w, pixmap_h, mouse_pos):

        left = text_rect.left()
        right = text_rect.right()
        #infoRect = QRect(0, 0, 200, 100)

        painter.drawImage(QPointF(left, text_rect.top()), file_pixmap.toImage())

        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        fm = QFontMetrics(font)
        font_h = fm.height()

        file_name = self.filename
        fileNameRect = painter.boundingRect(
            QRect(QPoint(left + pixmap_w + 10, text_rect.top()), QPoint(right - 10, text_rect.bottom())),
            Qt.TextWordWrap, file_name
        )

        rect = (left, text_rect.top(), fileNameRect.right(), max([fileNameRect.bottom(), text_rect.top() + pixmap_h]))
        is_mouse_in = (
            rect[0] <= mouse_pos[0] <= rect[2] and
            rect[1] <= mouse_pos[1] <= rect[3]
        )
        self.message_drawer.links.add((self, rect))

        if is_mouse_in:
            painter.setPen(QPen(QColor(self.message_drawer.delegate.LINK_COLOR_HOVER)))
            self.message_drawer.delegate.listView.cursor_need_cross = True
        else:
            painter.setPen(QPen(QColor(self.message_drawer.delegate.RESEND_COLOR)))

        painter.drawText(fileNameRect, Qt.TextWordWrap, file_name)

        # file size
        painter.setPen(QPen(QColor(self.message_drawer.delegate.RESEND_COLOR)))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        file_size = self.filesize
        fileSizeRect = painter.boundingRect(
            QRect(QPoint(fileNameRect.left(), fileNameRect.bottom()), QPoint(fileNameRect.right(), text_rect.bottom())),
            Qt.TextWordWrap, file_size)
        painter.drawText(fileSizeRect, Qt.TextWordWrap, file_size)


class QuoteFileLine(FileLine):

    first_word_left = 10




@contextmanager
def change_font(painter: QPainter, **kwargs):
    temp_pen = painter.pen()
    temp_font = painter.font()

    yield FontChanger(painter, **kwargs)

    painter.setPen(temp_pen)
    painter.setFont(temp_font)


class FontChanger:

    def __init__(self, painter: QPainter, **kwargs):
        self.painter = painter

        # font_size=12, text_color=self.mes_drawer.delegate.INFO_COLOR
        for name in ('simple_font', 'bold', 'font_size', 'text_color'):
            if name in kwargs:
                func = getattr(self, f'set_{name}', None)
                if func:
                    func(kwargs.get(name))

    def set_bold(self, value):
        font = self.painter.font()
        font.setBold(value)
        self.painter.setFont(font)

    def set_simple_font(self, _):
        font = QFont()
        self.painter.setFont(font)

    def set_font_size(self, value):
        font = self.painter.font()
        font_pixel_size = value
        if font_pixel_size < 3:
            font_pixel_size = 3
        font.setPixelSize(font_pixel_size)
        self.painter.setFont(font)

    def set_text_color(self, value):
        pen = self.painter.pen()
        pen.setColor(QColor(value))
        self.painter.setPen(pen)
