
from typing import List

from PyQt5.QtCore import QRect, QPoint
from PyQt5.QtGui import QPainter, QFontDatabase, QFont, QPen, QColor, QFontMetrics

from bp_chat.logic.datas.Message import Message
from bp_chat.gui import delegates

from .Selection import Selection
from .Line import FileLine, WordsLine, LineBase, QuoteLine, QuoteAuthor, QuoteFileLine, HeaderLine, FooterLine
from .Word import Word, LinkWord, WORD_TYPE_LINK, LineContinue


class MessageDrawer:

    FONT_SIZE = 13
    LETTER_SPACING = 95

    lines = None
    _lines: List[LineBase] = None
    current_size = None
    font_height = 16
    font_width = 8
    font = None
    fonts_database = None
    links = None
    _text_rect = None

    need_show_sender_name = False

    def __init__(self, message: Message, delegate: 'delegates.MessagesDictDelegate.MessagesDictDelegate'):
        self.delegate = delegate
        self.message = message
        if not MessageDrawer.fonts_database:
            database = QFontDatabase()
            loaded_font_id = database.addApplicationFont(":/images/data/images/RobotoMono-Regular.ttf")
            MessageDrawer.fonts_database = database
        self.font = MessageDrawer.fonts_database.font('Roboto Mono', "regular", self.FONT_SIZE)
        self.font.setLetterSpacing(0, self.LETTER_SPACING)
        font_pixel_size = self.FONT_SIZE
        if font_pixel_size < 3:
            font_pixel_size = 3
        self.font.setPixelSize(font_pixel_size)

    @property
    def letter_width(self):
        return self.font_width * self.LETTER_SPACING / 100.0

    def draw_message_lines(self, painter: QPainter, text_rect, selection_sorted):

        selection: Selection = self.delegate.selection
        self._text_rect = text_rect

        painter.setFont(self.font)
        temp_pen = painter.pen()

        mouse_pos = self.delegate.mouse_pos

        word_num = -1
        letter_width = self.letter_width

        # painter.drawLine(text_rect.left()-5, text_rect.top(),
        # text_rect.left()-5, text_rect.top() + self.current_size[1])

        for row, words, x, y, y_start in self.lines_gen(text_rect):

            has_left_line = getattr(words, 'first_word_left', False)
            if has_left_line:
                padding_last_bottom_2 = 0 #round(getattr(words, 'padding_last_bottom', 0) / 2)
                _y_start = y_start
                if hasattr(words, 'line_height'):
                    _y_start = y - getattr(words, 'line_height')
                painter.setPen(QPen(QColor(self.delegate.RESEND_COLOR), 3))
                painter.drawLine(QPoint(x-has_left_line, _y_start+padding_last_bottom_2),
                                 QPoint(x-has_left_line, y+padding_last_bottom_2))
                painter.setPen(temp_pen)

            last_w_drawn = False
            if hasattr(words, 'draw_line'):
                word_num, x, last_w_drawn = words.draw_line(self, painter, self.delegate,
                                              self.message, word_num, x, y, y_start,
                                              mouse_pos, selection, selection_sorted,
                                              self.font_width, letter_width, temp_pen, last_w_drawn)

            else:
                draw_func = getattr(words, 'draw', None)
                if draw_func:
                    rect = QRect(QPoint(x, y_start), QPoint(text_rect.right(), text_rect.bottom()))
                    draw_func(painter, rect, self.font_height, mouse_pos)

    def get_selected_lines(self, selection_sorted):

        selection: Selection = self.delegate.selection
        if not self._text_rect:
            return []

        new_lines = []

        word_num = -1
        letter_width = self.letter_width
        last_line = None
        for row, words, x, y, y_start in self.lines_gen(self._text_rect):

            if hasattr(words, 'get_selected_line'):
                new_line, word_num = words.get_selected_line(self.message, word_num, x, y, y_start, letter_width, selection, selection_sorted)
            else:
                new_line = []

            if len(new_line) > 0:
                if last_line and len(last_line) and type(last_line[-1]) == LineContinue:
                    last_line[:] = last_line[:-1] + new_line
                else:
                    new_lines.append(new_line)
                    last_line = new_line

        return new_lines

    def lines_gen(self, text_rect):

        top = text_rect.top()
        left = text_rect.left()
        row = 0
        last_words = None
        last_type = None
        y_start = top
        margin_last_bottom_last = 0

        if self.lines:
            for i, words, line_start_i in self.lines:
                x = left + getattr(words, 'first_word_left', 0)

                cur_type, y_start, y = self.calc_y(words, last_type, last_words, y_start)

                if last_type and cur_type != last_type:
                    if margin_last_bottom_last > 0:
                        y_start += margin_last_bottom_last
                        y += margin_last_bottom_last

                    margin_first_top = getattr(words, 'margin_first_top', 0)
                    if margin_first_top > 0:
                        y_start += margin_first_top
                        y += margin_first_top

                yield row, words, x, y, y_start

                row += 1

                y_start = y

                last_words, last_type = words, cur_type
                margin_last_bottom_last = getattr(words, 'margin_last_bottom', 0)

    def calc_y(self, words, last_type, last_words, y_start):
        y_add = self.font_height

        get_size_func = getattr(words, 'get_size', None)
        if get_size_func:
            sz = get_size_func(self.font_height)
            y_add = sz[1]

        cur_type = type(words)
        if cur_type != last_type:
            padding_first_top = getattr(words, 'padding_first_top', None)
            if padding_first_top:
                y_add += padding_first_top

            elif last_words:
                padding_last_bottom = getattr(last_words, 'padding_last_bottom', None)
                if padding_last_bottom:
                    y_add += padding_last_bottom

        y = y_start + y_add
        return cur_type, y_start, y

    def find_selection_start_word_pos(self, xxx, yyy):
        letter_width = self.letter_width

        word_num = -1
        for row, words, x, y, y_start in self.lines_gen(self._text_rect):

            if hasattr(words, 'find_selection_start_word_pos'):
                word_num, word_start = words.find_selection_start_word_pos(xxx, yyy, x, y_start, word_num, letter_width)
                if word_start is not None:
                    return word_num, word_start

            else:
                pass

        return 0, 0

    def find_selection_end_word_pos(self, xxx, yyy):
        letter_width = self.letter_width

        word_num = -1
        word_end = None
        for row, words, x, y, y_start in self.lines_gen(self._text_rect):

            if hasattr(words, 'find_selection_end_word_pos'):
                found, word_num, word_end = words.find_selection_end_word_pos(xxx, yyy, x, y_start, word_num, letter_width, word_end)
                if found:
                    return word_num, word_end
            else:
                pass

        return word_num, word_end

    def draw_quote_lines(self, painter: QPainter, width):
        pass

    def recalc_height_for_width(self, width):
        text_rect = self._text_rect

        if text_rect and self.current_size and self.current_size[0] == width:
            return self.current_size[1]

        self.update_lines(width)

        if not text_rect:
            text_rect = QRect(0, 0, 30, 16*3)

        cur_h = 0
        for row, words, x, y, y_start in self.lines_gen(text_rect):
            get_size_func = getattr(words, 'get_size', None)
            if get_size_func:
                size = get_size_func(self.font_height)
            else:
                size = 0, self.font_height
            cur_h += size[1]

        font = QFont()
        font.setBold(False)
        font.setPixelSize(12)
        font_h = QFontMetrics(font).height()

        h = cur_h + font_h
        self.current_size = (width, h)
        return h

    def update_lines(self, width):
        if width < 0: # FIXME cant use it: or (self.lines is not None and self.current_size is not None and self.current_size[0] == width):
            return False

        max_len = int(width / self.font_width)
        if self._lines is None:

            _text = self.message.get_text()

            _lines = [WordsLine(self.split_line(line)) for line in _text.split('\n')]

            file = self.message.file
            has_file = file is not None and len(file) > 1
            if has_file:
                filename = self.message.getFileName()
                file_line = FileLine(self.message.getFile(), filename, self.message.getFileSize(), self)
                _lines.insert(0, file_line)
                if _text == filename:
                    _lines = _lines[:1]

            quote = self.message.quote
            if quote:
                _quote_text = self.message.get_quote_text()
                if not _quote_text:
                    _quote_text = ''
                _quote_lines: List[LineBase] = [QuoteLine(self.split_line(line), quote)
                                                for line in _quote_text.split('\n')]
                _quote_author: List[LineBase] = [QuoteAuthor(quote, self)]

                quote_filename = self.message.getFileName()
                quote_file = self.message.getFile()
                quote_file_size = self.message.getFileSize()
                _quote_file: List[LineBase] = []
                if quote_file and quote_file not in (0, '0'):
                    _quote_file.append(QuoteFileLine(quote_file, quote_filename, quote_file_size, self))

                _lines = _quote_author + _quote_file + _quote_lines + _lines

            self._lines = [HeaderLine(self.message, self)] + _lines + [FooterLine(self.message, self)]
        else:
            _lines = self._lines

        self.links = set()

        new_lines = []
        _lines: List[LineBase]
        for i, words in enumerate(_lines):
            new_words = self.make_line([], words)

            current_len = 0
            last_i = 0

            if hasattr(words, '__iter__'):
                words: WordsLine
                for j, w in enumerate(words):
                    d = 0 if j == 0 else 1
                    d += len(w)

                    if current_len + d > max_len:
                        new_words.append(LineContinue('>'))
                        new_lines.append((i, new_words, last_i))
                        last_i += current_len
                        current_len = d
                        new_words = self.make_line([w], words)
                    else:
                        current_len += d
                        new_words.append(w)
            else:
                new_words = words

            if current_len > 0 or True:
                new_lines.append((i, new_words, last_i))

        # links = []
        # for k, (i, new_words, last_i) in enumerate(new_lines):
        #     j = 0
        #     if hasattr(new_words, '__iter__'):
        #         for w in new_words:
        #             d = len(w)
        #             if w.word_type == WORD_TYPE_LINK:
        #                 w: LinkWord
        #                 rect = (j, k, j+d, k)
        #                 links.append((w.url, rect))
        #             j += d + 1
        #     else:
        #         pass

        #self.links = links

        self.lines = new_lines
        return True

    @staticmethod
    def make_line(lst, line):
        if type(line) == QuoteLine:
            line: QuoteLine
            return QuoteLine(lst, line.quote)
        else:
            return WordsLine(lst)

    def get_word(self, x, y):
        if x < 0:
            return

        words = self.get_line(y)
        if not words:
            return None

        x = int(x / (self.font_width * self.LETTER_SPACING / 100.0))

        i = 0
        if hasattr(words, '__iter__'):

            for w in words:
                d = len(w)
                if i <= x <= i + d:
                    return w

                i += d + 1

    def get_line(self, y):
        if not self.lines:
            return

        y_start = 0
        for i, words, line_start_i in self.lines: # FIXME not by gen

            dy = self.font_height
            get_size_func = getattr(words, 'get_size', None)
            if get_size_func:
                sz = get_size_func(self.font_height)
                dy = sz[1]

            yy = y_start + dy
            if y_start <= y < yy:
                return words

            y_start = yy

    def split_line(self, line):
        _words = line.split(' ')
        new_words = []
        for w in _words:
            if type(w) == int:
                continue

            w, link = self.get_link_from_word(w)
            if link:
                w = LinkWord(w, link)
            else:
                w = Word(w)

            new_words.append(w)
        return new_words

    @staticmethod
    def get_link_from_word(word):
        link = None
        if word.startswith('https://') or word.startswith('http://'):
            link = word
        elif word.startswith('#'):
            if word.startswith('#INPUT_CALL:'):
                _from = word[len('#INPUT_CALL:'):]
                link = word
                word = 'Входящий звонок от ' + _from
        return word, link
