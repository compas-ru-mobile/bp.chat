from copy import copy
from PyQt5.QtCore import QPoint

from bp_chat.logic.datas.Message import Message
from .. import delegates


class Selection:

    _selection = None
    _selection_started = False

    def __init__(self, messages_delegate: 'delegates.MessagesDictDelegate.MessagesDictDelegate'):
        self.messages_delegate = messages_delegate

    def clear(self):
        boo = True if self._selection else False
        self._selection = None
        return boo

    def get_selected_messages(self):
        _messages = self.messages_delegate.get_messages()
        selection_sorted = self.get_now_sorted()
        new_messages = []
        for mes in _messages:
            mes_drawer = self.messages_delegate.get_message_drawer(mes)
            if mes_drawer:
                lines = mes_drawer.get_selected_lines(selection_sorted)
                if len(lines) > 0:
                    new_messages.append((mes, lines))
        return new_messages

    def start(self, event_pos):
        self._selection_started = True
        self._selection = [event_pos.x(), event_pos.y(),
                           event_pos.x(), event_pos.y()]

    def update_started(self, event_pos):
        if self._selection_started and self._selection:
            self._selection[2] = event_pos.x()
            self._selection[3] = event_pos.y()

    def fin(self, event_pos):
        if self._selection_started:
            self._selection_started = False

            if not self.update_selection_and_sort(event_pos):
                self._selection = None
                return True

            selection_start = self.find_selection_start(QPoint(self._selection[0], self._selection[1]))
            selection_end = self.find_selection_end(QPoint(self._selection[2], self._selection[3]))

            self._selection = [selection_start, selection_end]
            return True

    @classmethod
    def is_word_in_selection(cls, mes_id, word_num, word_rect, selection_sorted, mes_drawer):
        if not selection_sorted:
            return False

        boo = False
        word_start = word_end = None

        if len(selection_sorted) == 4:
            is_in_top = word_rect.top() <= selection_sorted[1] < word_rect.bottom()
            is_in_bottom = word_rect.top() <= selection_sorted[3] < word_rect.bottom()

            if (is_in_top or is_in_bottom or
                selection_sorted[1] <= word_rect.top() <= word_rect.bottom() <= selection_sorted[3]
            ):
                boo = True

                if is_in_top:
                    if selection_sorted[0] > word_rect.right():
                        boo = False
                    else:
                        d = selection_sorted[0] - word_rect.left()
                        if d > 0:
                            word_start = int(d / mes_drawer.letter_width)

                if is_in_bottom:
                    if selection_sorted[2] < word_rect.left():
                        boo = False
                    else:
                        d = word_rect.right() - selection_sorted[2]
                        if d > 0:
                            word_end = int((word_rect.width()-d) / mes_drawer.letter_width)

        elif selection_sorted[0] and selection_sorted[1]:
            selection_start_mess, selection_start_word = selection_sorted[0]
            selection_end_mess, selection_end_word = selection_sorted[1]

            if selection_start_mess.mes_id <= mes_id <= selection_end_mess.mes_id:
                boo = True
                if selection_start_mess.mes_id == mes_id:
                    if selection_start_word == None or word_num < selection_start_word[0]:
                        boo = False
                    elif word_num == selection_start_word[0] and selection_start_word[1] != None:
                        word_start = selection_start_word[1]

                if selection_end_mess.mes_id == mes_id:
                    if selection_end_word == None or word_num > selection_end_word[0]:
                        boo = False
                    elif word_num == selection_end_word[0] and selection_end_word[1] != None:
                        word_end = selection_end_word[1]

        if boo and (word_start != None or word_end != None):
            boo = (boo, word_start, word_end)

        return boo

    def get_now_sorted(self):
        selection = self._selection
        if selection and len(selection) == 4:
            selection = copy(selection)
            self.sort_selection(selection)
        return selection

    def find_selection_start(self, pos):
        message, mes_drawer = self.find_mes_and_drawer(pos)
        if message and mes_drawer:
            mes_pos = mes_drawer.find_selection_start_word_pos(pos.x(), pos.y())
            return message, mes_pos

    def find_selection_end(self, pos):
        message, mes_drawer = self.find_mes_and_drawer(pos)
        if message and mes_drawer:
            mes_pos = mes_drawer.find_selection_end_word_pos(pos.x(), pos.y())
            return message, mes_pos

    def find_mes_and_drawer(self, pos):
        ind = self.messages_delegate.listView.indexAt(pos)

        message: Message = ind.data()
        mes_drawer = self.messages_delegate.get_message_drawer(message)

        return message, mes_drawer

    def update_selection_and_sort(self, pos):
        if not self._selection:
            return False
        if abs(pos.x() - self._selection[0]) < 4 and pos.y() == self._selection[1]:
            return False
        self._selection[2] = pos.x()
        self._selection[3] = pos.y()
        self.sort_selection(self._selection)
        return True

    def sort_selection(self, selection):
        self.sort_2_items(selection, 0, 2)
        self.sort_2_items(selection, 1, 3)

    def sort_2_items(self, lst, i1, i2):
        lst[i1], lst[i2] = (
            min(lst[i1], lst[i2]),
            max(lst[i1], lst[i2])
        )

