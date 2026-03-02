#
# from datetime import datetime
#
# import webbrowser
#
# from PyQt5.QtWidgets import QWidget, QItemDelegate, QStyle, QStyledItemDelegate
# from PyQt5.QtGui import QColor, QPainter, QIcon, QPen, QTextDocument, QAbstractTextDocumentLayout, QCursor, QFontMetrics
# from PyQt5.QtCore import Qt, QAbstractListModel, QSize, QPointF, QRect, QRectF, QPoint, pyqtSignal, QItemSelectionModel, QItemSelection
#
# from ...logic.chat_api.ChatApi import ChatApi
# from ...logic.chat_api.DeliveredSender import DeliveredSender
# from ...logic.chat_api import ChatApiCommon
# from ...logic.datas.Message import Message
# from ..common.draw_funcs import pixmap_from_icon_rounded, icon_from_file
#
# from threading import Timer
# from os.path import exists, join
#
#
# class MessagesDictDelegate(QStyledItemDelegate):
#
#     LINK_COLOR = '#0078d7'
#     RESEND_COLOR = '#3078ab'
#
#     avatar_r = 20
#     padding_x = 10
#     padding_y = 10
#     spacing = 10
#
#     def __init__(self, listView, clear):
#         self.listView = listView
#         self.clear = clear
#         self.images = {}
#         super().__init__(listView)
#
#     def getRightAdd(self):
#         return self.listView.width_add
#
#     def paint(self, painter, option, index):
#         deliveredSender = DeliveredSender.getInstance()
#         deliveredSender.setMessagesAdapter(self)
#
#         left, top, right, bottom = option.rect.left(), option.rect.top(), option.rect.right(), option.rect.bottom()
#
#         painter.setRenderHint(QPainter.Antialiasing)
#
#         # FIXME will be more good...
#         messages = self.get_messages()
#         message = messages[index.row()]
#
#         if index.row() == len(messages)-1:
#             ChatApi.instance().clearGettingLastMessages()
#
#         last_message = None
#         if (index.row()-1) >= 0:
#             mess = messages[index.row()-1]
#             if hasattr(mess, 'getSender'):
#                 last_message = mess
#
#         if isinstance(message, LoadMessagesButton):
#             painter.drawText(option.rect, Qt.AlignCenter, message.text)
#             painter.drawRect(left+11, top+4, right-left-22 + self.getRightAdd(), bottom-top-8)
#             return
#
#         text = message.text
#         quote = message.quote
#         file = message.file
#         has_file = file != None and len(file) > 1
#
#         # Get delivered for background:
#         delivered_icon = None
#         current_user_id = ChatApi.instance().getCurrentUserId()
#         if current_user_id == message.sender_id:
#             background_color = ChatApiCommon.COLOR_MY_MESSAGE
#             delivered_icon = icon_from_file("check")
#             if message.getDelivered():
#                 delivered_icon = icon_from_file("check_all")
#         else:
#             if not message.getDelivered(): #// pos >= badges_start
#                 background_color = ChatApiCommon.COLOR_MESSAGE_NOT_READED
#                 deliveredSender.add_by_gui(message.mes_id)
#             else:
#                 background_color = QColor(255, 255, 255)
#
#         allow_select = self.listView.allow_select
#
#         inds = self.listView.selectedIndexes()
#         for ind in inds:
#             if ind.row() == index.row():
#                 background_color = QColor('#fae298')
#
#         _rect = option.rect.adjusted(1, 1, -1, -1)
#         _rect.setTop(_rect.top() - 1)
#         _rect.setBottom(_rect.bottom()+1)
#         painter.fillRect(_rect, background_color)
#
#         font = painter.font()
#         font.setPixelSize(14)
#         painter.setFont(font)
#         fm = QFontMetrics(font)
#
#         # --------- avatar and label ----------
#         if last_message is None or last_message.getSender() != message.getSender():
#             # аватар - фон
#             painter.setPen(QColor('#e7e6bc'))
#             painter.setBrush(QColor('#e7e6bc'))
#             painter.drawEllipse(QPointF(left + self.avatar_r + self.padding_x,
#                                         top + self.avatar_r + self.padding_y),
#                                 self.avatar_r, self.avatar_r)
#
#             # аватар - изображение
#             user = message.getSender()
#             btm = None
#             if user:
#                 up = user.profile
#                 btm = up.getBitmap()
#             offset_x = offset_y = 0  # FIXME hack
#             pixmap = None
#             if btm:
#                 pixmap = pixmap_from_icon_rounded(btm, to_size=(self.avatar_r*2, self.avatar_r*2))
#                 if pixmap:
#                     offset_x = (pixmap.width() - self.avatar_r*2) / 2
#                     offset_y = (pixmap.height() - self.avatar_r*2) / 2
#             if not pixmap:
#                 icon = icon_from_file("user")
#                 pixmap = icon.pixmap(QSize(self.avatar_r*2, self.avatar_r*2))
#             painter.drawImage(QPointF((left + self.padding_x) - offset_x, (top + self.padding_y) - offset_y), pixmap.toImage())
#
#             # text with nickname
#             painter.setPen(QColor(30, 30, 30))
#             font = painter.font()
#             font.setBold(True)
#             painter.setFont(font)
#             sender_nickname = "{}".format(message.getSenderName())  # message.getTimeString()
#             infoRect = painter.boundingRect(QRect(QPoint(left + self.avatar_r*2 + self.padding_x + self.spacing, top + self.padding_y),
#                                                   QPoint(right - self.padding_x, top + self.padding_y)),
#                                             Qt.TextWordWrap, sender_nickname)
#             infoRect = painter.drawText(infoRect, Qt.TextWordWrap, sender_nickname)
#         else:
#             infoRect = QRect(QRect(QPoint(left + self.padding_x, top + self.padding_y),
#                                    QPoint(right - self.padding_x, top + self.padding_y)))
#         # -------------------------------------
#
#         # right bottom text with date and delivered
#         painter.setPen(QColor(128, 128, 128))
#         font = painter.font()
#         font.setBold(False)
#         font.setPixelSize(12)
#         painter.setFont(font)
#
#         # render icon delivered
#         if delivered_icon is not None:
#             avatar_pixmap = delivered_icon.pixmap(QSize(QFontMetrics(font).height(), QFontMetrics(font).height()))
#             painter.drawImage(QPointF(right - (QFontMetrics(font).height() + self.padding_x) + self.listView.width_add, bottom - (self.padding_y + 10)), avatar_pixmap.toImage())  # FIXME 5...
#
#         date_text = "{}".format(message.getTimeString())
#         date_text_width = QFontMetrics(font).width(date_text)
#
#         _top_left = QPoint(right - (date_text_width + self.padding_x + 5 + QFontMetrics(font).height()) + self.listView.width_add,
#                            bottom - (self.padding_y + 10))
#         dateTextRect = QRect(_top_left, QSize(date_text_width, QFontMetrics(font).height()))
#         painter.drawText(dateTextRect, Qt.AlignLeft, date_text)
#
#         # FIXME
#         font = painter.font()
#         font.setPixelSize(14)
#         painter.setFont(font)
#
#         if has_file:
#             pixmap_w = pixmap_h = fm.height() * 2
#
#             # _fullpath = join(ChatApiCommon.getDownloadsDirectoryPath(), message.getFileName())
#             _file_uuid = message.getFile()
#             icon = self.images.get(_file_uuid)
#             if icon:
#                 _w = self.listView.width() - 300
#                 if _w > 300:
#                     _w = 300
#                 isz = icon.actualSize(QSize(_w, self.listView.height()))
#                 if isz.width() > 0 and isz.height() > 0:
#                     pixmap_w, pixmap_h = isz.width(), isz.height()
#             else:
#                 _fullpath = ChatApiCommon.getDownloadsFilePath(message.getFileName(), _file_uuid)
#                 file_exists = exists(_fullpath)
#
#                 # файл - изображение
#                 if file_exists:
#                     _lower_fullpath = _fullpath.lower()
#                     if _lower_fullpath.endswith('.jpg') or _lower_fullpath.endswith('.png'):
#                         icon = QIcon(_fullpath)
#                         self.images[_file_uuid] = icon
#                         _w = self.listView.width() - 300
#                         if _w > 300:
#                             _w = 300
#                         isz = icon.actualSize(QSize(_w, self.listView.height()))
#                         if isz.width() > 0 and isz.height() > 0:
#                             pixmap_w, pixmap_h = isz.width(), isz.height()
#                         else:
#                             icon = icon_from_file("file")
#                     else:
#                         icon = icon_from_file("file")
#
#                 else:
#                     icon = icon_from_file("download_file")
#
#             file_pixmap = icon.pixmap(QSize(pixmap_w, pixmap_h))
#             painter.drawImage(QPointF(left + self.avatar_r*2 + self.padding_x + self.spacing,
#                                       infoRect.bottom()),
#                               file_pixmap.toImage())
#
#             # file name
#             painter.setPen(QPen(QColor(self.RESEND_COLOR)))
#             font = painter.font()
#             font.setBold(True)
#             painter.setFont(font)
#             file_name = message.getFileName()
#             fileNameRect = painter.boundingRect(
#                 QRect(QPoint(left + self.avatar_r*2 + self.padding_x + self.spacing + file_pixmap.width(), infoRect.bottom()),
#                       QPoint(right - self.padding_x, infoRect.bottom())),
#                 Qt.TextWordWrap, file_name)
#             painter.drawText(fileNameRect, Qt.TextWordWrap, file_name)
#
#             # file size
#             painter.setPen(QPen(QColor(self.RESEND_COLOR)))
#             font = painter.font()
#             font.setBold(True)
#             painter.setFont(font)
#             file_size = message.getFileSize()
#             fileSizeRect = painter.boundingRect(
#                 QRect(QPoint(left + self.avatar_r * 2 + self.padding_x + self.spacing + file_pixmap.width(), fileNameRect.bottom()),
#                       QPoint(right - self.padding_x, fileNameRect.bottom())),
#                 Qt.TextWordWrap, file_name)
#             painter.drawText(fileSizeRect, Qt.TextWordWrap, file_size)
#
#         elif quote:
#             # self.drawQuoteMessage(painter, option, message)
#             spacing_quote = self.spacing*2
#
#             # инфо об отправителе пересылаемого сообщения)
#             painter.setPen(QPen(QColor(self.RESEND_COLOR)))
#             font = painter.font()
#             font.setBold(True)
#             painter.setFont(font)
#             info_quote_text = quote.getSenderName()
#             infoQuoteRect = painter.boundingRect(
#                 QRect(QPoint(left + self.avatar_r*2 + self.padding_x + spacing_quote, infoRect.bottom()),
#                       QPoint(right - self.padding_x, infoRect.bottom())),
#                 Qt.AlignLeft, info_quote_text)
#             painter.drawText(infoQuoteRect, Qt.AlignLeft, info_quote_text)
#
#             # FIXME !=None
#             if quote.file != None and len(quote.file) > 1:
#                 #_fullpath = join(ChatApiCommon.getDownloadsDirectoryPath(), message.getFileName())
#                 _fullpath = ChatApiCommon.getDownloadsFilePath(message.getFileName(), message.getFile())
#                 file_exists = exists(_fullpath)
#
#                 # файл - изображение
#                 if file_exists:
#                     icon = icon_from_file("file")
#                 else:
#                     icon = icon_from_file("download_file")
#                 pixmap_h = fm.height() * 2
#                 file_pixmap = icon.pixmap(QSize(pixmap_h, pixmap_h))
#                 painter.drawImage(QPointF(left + self.avatar_r * 2 + self.padding_x + spacing_quote,
#                                           infoQuoteRect.bottom()),
#                                   file_pixmap.toImage())
#
#                 # file name
#                 painter.setPen(QPen(QColor(self.RESEND_COLOR)))
#                 font = painter.font()
#                 font.setBold(True)
#                 painter.setFont(font)
#                 file_name = message.getFileName()
#                 fileNameRect = painter.boundingRect(
#                     QRect(QPoint(left + self.avatar_r * 2 + self.padding_x + spacing_quote + file_pixmap.width(),
#                                  infoQuoteRect.bottom()),
#                           QPoint(right - self.padding_x, infoQuoteRect.bottom())),
#                     Qt.TextWordWrap, file_name)
#                 painter.drawText(fileNameRect, Qt.TextWordWrap, file_name)
#
#                 # file size
#                 painter.setPen(QPen(QColor(self.RESEND_COLOR)))
#                 font = painter.font()
#                 font.setBold(True)
#                 painter.setFont(font)
#                 file_size = Message.fileSizeToStringFromRaw(quote.fileSize) # FIXME
#                 fileSizeRect = painter.boundingRect(
#                     QRect(QPoint(left + self.avatar_r * 2 + self.padding_x + spacing_quote + file_pixmap.width(),
#                                  fileNameRect.bottom()),
#                           QPoint(right - self.padding_x, fileNameRect.bottom())),
#                     Qt.TextWordWrap, file_name)
#                 painter.drawText(fileSizeRect, Qt.TextWordWrap, file_size)
#
#                 bottom_content = fileSizeRect.bottom()
#             else:
#                 # пересылаемый текст
#                 rect = QRect(QPoint(left + self.avatar_r*2 + self.padding_x + spacing_quote, infoQuoteRect.bottom()),
#                              QPoint(right - self.padding_x, infoQuoteRect.bottom()))
#
#                 bottom_content = 0
#
#                 last_line_rect = self.drawText(painter, quote.message, rect, message, allow_select=allow_select, quote=True)
#                 bottom_content = last_line_rect.bottom()
#
#             # дополнительный текст
#             rect = QRect(QPoint(left + self.avatar_r * 2 + self.padding_x + self.spacing, bottom_content + 5), # FIXME
#                          QPoint(right - self.padding_x, bottom_content))
#
#             self.drawText(painter, text, rect, message, allow_select=allow_select)
#
#             # вертикальная линия
#             painter.setPen(QPen(QColor(self.RESEND_COLOR), 3))
#             painter.drawLine(QPointF(left + self.avatar_r * 2 + self.padding_x + self.spacing + 3, infoQuoteRect.top()),
#                              QPointF(left + self.avatar_r * 2 + self.padding_x + self.spacing + 3, bottom_content))
#         else:
#             rect = QRect(QPoint(left + self.avatar_r * 2 + self.padding_x + self.spacing, infoRect.bottom()),
#                          QPoint(right - self.padding_x + self.getRightAdd(), infoRect.bottom()))
#
#             self.drawText(painter, text, rect, message, allow_select=allow_select)
#
#     def drawText(self, painter, text, rect, message, allow_select=False, quote=False):
#         font = painter.font()
#         font.setBold(False)
#         selection_text = ''
#         last_rect = rect
#         i = -1
#         for is_new_line, r, char_seq, is_selection, is_link in self.genRectText(font, text, rect, message, allow_select=allow_select):
#             i += 1
#             painter.setPen(QColor(30, 30, 30))
#             # if message.mes_id in (21664, '21664', 21663, '21663'):
#             if is_link:
#                 painter.setPen(QColor(self.LINK_COLOR))
#                 # painter.setPen(QColor('#0000FF'))
#             if is_selection:
#                 painter.setPen(QColor('#FFFFFF'))
#                 painter.fillRect(r, QColor('#0078d7'))
#                 if is_new_line and i > 0:
#                     selection_text += '\n'
#                 selection_text += char_seq
#             font = painter.font()
#             font.setBold(False)
#             painter.setFont(font)
#             painter.drawText(r, Qt.AlignLeft, char_seq)
#             last_rect = r
#
#         add_quote = ""
#         if quote:
#             add_quote = "_quote"
#         if selection_text:
#             self.listView.addSelectionText(selection_text, str(message.mes_id) + add_quote)
#         else:
#             self.listView.removeSelectionText(str(message.mes_id) + add_quote)
#
#         return last_rect
#
#     def prepareText(self, text):
#         words = []
#         word = ''
#         for char in text:
#             if char in ('\n', '\t', '\u0020'):
#                 if len(word) > 0:
#                     words.append(word)
#                 words.append(char)
#                 word = ''
#                 continue
#             word += char
#         if len(word) > 0:
#             words.append(word)
#         return words
#
#     def genRectText(self, font, text, rect, message, allow_select=False):
#         f = font
#         fm = QFontMetrics(f)
#
#         _lines = self.get_lines_from_words(font, text, rect)
#         links = self.getLinksDict([li for li, _ in _lines], message.getLinks())
#         top_left = rect.topLeft()
#         no_chars_in_line_i = 0
#         for line, is_new_line  in _lines:
#             #is_new_line = True
#             chars_in_line = ''
#             chars_r = None
#             for word, link in self.defineLinks(line, links):
#                 is_link = link
#                 if not is_link:
#                     chars_in_line += word
#                     continue
#                 else:
#                     if len(chars_in_line) > 0:
#                         # chars_r = fm.boundingRect(chars_in_line)
#                         chars_r = QRect(top_left, QSize(fm.width(chars_in_line), fm.height()))
#                         # chars_r.moveTopLeft(top_left)
#                         if allow_select:
#                             for chars_r, char_seq, is_selection in self.getSelectionRect(font, chars_r, chars_in_line):
#                                 yield is_new_line, chars_r, char_seq, is_selection, False
#                                 is_new_line = False
#                         else:
#                             yield is_new_line, chars_r, chars_in_line, allow_select, False
#                             is_new_line = False
#                         chars_in_line = ''
#                         top_left = QPoint(chars_r.right(), chars_r.top())
#                     _link = word
#                     chars_r = fm.boundingRect(_link)
#                     chars_r.moveTopLeft(top_left)
#                     if allow_select:
#                         for chars_r, char_seq, is_selection in self.getSelectionRect(font, chars_r, _link):
#                             yield is_new_line, chars_r, char_seq, is_selection, is_link
#                             is_new_line = False
#                     else:
#                         yield is_new_line, chars_r, _link, allow_select, is_link
#                         is_new_line = False
#                     top_left = QPoint(chars_r.right(), chars_r.top())
#
#             if len(chars_in_line) > 0:
#                 no_chars_in_line_i = 0
#             else:
#                 no_chars_in_line_i += 1
#                 if no_chars_in_line_i == 1:
#                     chars_in_line = '\u0020'
#
#             if no_chars_in_line_i <= 1:
#                 # chars_in_line = ''.join(line)
#                 # chars_r = fm.boundingRect(chars_in_line)
#                 chars_r = QRect(top_left, QSize(fm.width(chars_in_line), fm.height()))
#                 # if no_chars_in_line_i > 0:
#                 #     chars_in_line = ''
#                 # chars_r.moveTopLeft(top_left)
#                 if allow_select:
#                     for chars_r, char_seq, is_selection in self.getSelectionRect(font, chars_r, chars_in_line):
#                         yield is_new_line, chars_r, char_seq, is_selection, False
#                         is_new_line = False
#                 else:
#                     yield is_new_line, chars_r, chars_in_line, allow_select, False
#                     is_new_line = False
#
#             if chars_r:
#                 top_left = QPoint(rect.left(), chars_r.bottom())
#
#     def getLinksDict(self, lines, links):
#         words = sum(lines, [])
#
#         d = {}
#
#         for link in links:
#             part_link = ''
#             for word in words:
#                 if not word:
#                     continue
#                 if word == link:
#                     d[word] = link
#                 else:
#                     part = link.partition(word)
#                     if part_link == part[0]:
#                         if part_link:
#                             d[part_link] = link
#                         if len(part[2]) == 0:
#                             d[word] = link
#                             break
#                         else:
#                             part_link = word
#                     else:
#                         part_link = ''
#         return d
#
#     def defineLinks(self, line, links):
#         for word in line:
#             yield word, links.get(word, None)
#
#     def get_lines_from_words(self, font, text, rect):
#         f = font
#         fm = QFontMetrics(f)
#
#         space = '\u0020'
#         len_space = 0
#         tab_width = fm.width(space*4)
#
#         last_right = rect.left()
#         lines = []
#         line = []
#         is_new_line = False
#         for word in self.prepareText(text):
#             if word == '\n':
#                 lines.append((line, is_new_line))
#                 is_new_line = True
#                 line = []
#                 last_right = rect.left()
#             elif word == '\t':
#                 if tab_width > (rect.right() - last_right):
#                     if (rect.right() - last_right) <= 0:
#                         lines.append((line, is_new_line))
#                         is_new_line = False
#                         line = [space*4]
#                         last_right = rect.left() + tab_width
#                     else:
#                         line.append(' ')
#                         lines.append((line, is_new_line))
#                         is_new_line = False
#                         line = []
#                         last_right = rect.left()
#                 else:
#                     line.append(space*4)
#                     last_right += tab_width
#             elif word == space:
#                 len_space += 1
#                 continue
#             else:
#                 if len_space >= 1:
#                     space_w = fm.width(space*len_space)
#                     if space_w > (rect.right() - last_right):
#                         if (rect.right() - last_right) <= 0:
#                             lines.append((line, is_new_line))
#                             is_new_line = False
#                             line = [space*len_space]
#                             last_right = rect.left() + space_w
#                         else:
#                             line.append(' ')
#                             lines.append((line, is_new_line))
#                             is_new_line = False
#                             line = []
#                             last_right = rect.left()
#                     else:
#                         line.append(space*len_space)
#                         last_right += space_w
#                     len_space = 0
#                 _, in_rect, end = self.smart_split(font, rect.left(), rect, word)
#                 while end:
#                     if len(line) > 0:
#                         lines.append((line, is_new_line)) # FIXME must be empty line, because tab and spaces...
#                         is_new_line = False
#                         line = []
#                         last_right = rect.left()
#                     lines.append(([in_rect], is_new_line))
#                     is_new_line = False
#                     s, in_rect, end = self.smart_split(font, rect.left(), rect, end)
#
#                 len_word = fm.width(in_rect)
#                 if len_word > (rect.right() - last_right):
#                     lines.append((line, is_new_line))
#                     is_new_line = False
#                     line = [in_rect]
#                     last_right = rect.left() + len_word
#                 else:
#                     line.append(in_rect)
#                     last_right += len_word
#         if len(line) > 0:
#             lines.append((line, is_new_line))
#             is_new_line = False
#         return lines
#
#     def smart_split(self, font, left, rect, word):
#         f = font
#         fm = QFontMetrics(f)
#
#         start_chars = ''
#         in_rect = ''
#         last_x = left
#         _len = len(word)
#         for i, w in enumerate(word):
#             cr = fm.boundingRect(w)
#             try:
#                 rb = fm.rightBearing(w)
#             except Exception:
#                 #raise
#                 rb = fm.rightBearing("W") # FIXME: smiles !!!
#
#             if rect.left() < last_x + cr.width():
#                 if last_x + cr.width() <= rect.right() + 1: # FIXME +1
#                     in_rect += w
#             else:
#                 start_chars += w
#             last_x += cr.width() + rb
#
#         return start_chars, in_rect, word[len(start_chars)+len(in_rect):]
#
#     def getSelectionRect(self, font, rect, word):
#         _pressed_mouse_pos = self.listView._pressed_mouse_pos
#         _current_mouse_pos = self.listView._current_mouse_pos
#
#         if (_pressed_mouse_pos is None or _current_mouse_pos is None): #or \
#                         # (max(_pressed_mouse_pos.x(), _current_mouse_pos.x()) - min(_pressed_mouse_pos.x(),
#                         #                                                            _current_mouse_pos.x())) < .5 or \
#                         # (max(_pressed_mouse_pos.y(), _current_mouse_pos.y()) - min(_pressed_mouse_pos.y(),
#                         #                                                            _current_mouse_pos.y())) < .5:
#             return [[rect, word, False]]
#
#         if min(_current_mouse_pos.y(), _pressed_mouse_pos.y()) > rect.bottom() \
#                 or max(_current_mouse_pos.y(), _pressed_mouse_pos.y()) < rect.top():
#                 # or min(_current_mouse_pos.x(), _pressed_mouse_pos.x()) > rect.right() \
#                 # or max(_current_mouse_pos.x(), _pressed_mouse_pos.x()) < rect.left():
#             return [[rect, word, False]]
#
#         selection_rect = None
#
#         if rect.bottom() > _pressed_mouse_pos.y() > rect.top() and rect.bottom() > _current_mouse_pos.y() > rect.top():
#             selection_rect = QRect(QPoint(min(_current_mouse_pos.x(), _pressed_mouse_pos.x()),
#                                           rect.top()),
#                                    QPoint(max(_current_mouse_pos.x(), _pressed_mouse_pos.x()),
#                                           rect.bottom()))
#         elif not rect.contains(_current_mouse_pos) and rect.bottom() > _pressed_mouse_pos.y() > rect.top():
#             if _current_mouse_pos.y() > rect.bottom():
#                 selection_rect = QRect(QPoint(_pressed_mouse_pos.x(), rect.top()), rect.bottomRight())
#             elif rect.top() > _current_mouse_pos.y():
#                 selection_rect = QRect(rect.topLeft(), QPoint(_pressed_mouse_pos.x(), rect.bottom()))
#         elif not rect.contains(_pressed_mouse_pos) and rect.bottom() > _current_mouse_pos.y() > rect.top():
#             if _pressed_mouse_pos.y() > rect.bottom():
#                 br = rect.bottomRight()
#                 selection_rect = QRect(QPoint(_current_mouse_pos.x(), rect.top()), QPoint(br.x()+5, br.y()))
#             elif rect.top() > _pressed_mouse_pos.y():
#                 selection_rect = QRect(rect.topLeft(), QPoint(_current_mouse_pos.x(), rect.bottom()))
#         else:
#             return [[rect, word, True]]
#
#         f = font
#         fm = QFontMetrics(f)
#
#         ret = []
#         if selection_rect is not None:
#             top_left = rect.topLeft()
#             for i, char_seq in enumerate(self.smart_split(font, rect.left(), selection_rect, word)):
#                 is_select = i == 1
#                 if len(char_seq) > 0:
#                     chars_rect = QRect(top_left, QSize(fm.width(char_seq), fm.height()))
#                     ret.append([chars_rect, char_seq, is_select])
#                     top_left = QPoint(chars_rect.right() + 1, chars_rect.top()) # FIXME *2
#
#         return ret or [[rect, word, False]]
#
#     def sizeHint(self, option, index):
#         # return QSize(option.rect.right(), 60)
#
#         f = option.font
#         # fm = QFontMetrics(f)
#
#         flags = Qt.TextWrapAnywhere
#
#         message = index.data()
#
#         if isinstance(message, LoadMessagesButton):
#             return QSize(option.rect.right(), 40)
#
#         quote = message.quote
#         file = message.file
#         has_file = file != None and len(file) > 1
#
#         last_message = None
#         if (index.row() - 1) >= 0:
#             messages = self.get_messages()
#             mess = messages[index.row() - 1]
#             if hasattr(mess, 'getSender'):
#                 last_message = mess
#
#         right_bottom_date_h = QSize(0, 10)
#         min_height = 25
#         info_size = QSize(0, 0)
#         if last_message is None or last_message.getSender() != message.getSender():
#             min_height = (self.avatar_r + self.padding_y) * 2
#
#             f.setPixelSize(14)
#             f.setBold(True)
#             fm = QFontMetrics(f)
#             boundRect = fm.boundingRect
#
#             info_text = "{} {}".format(message.getSenderName(), message.getTimeString())
#             info_size = boundRect(QRect(option.rect.left() + self.avatar_r*2 + self.padding_x + self.spacing,
#                                         0, option.rect.right() - self.padding_x + self.getRightAdd(), 0),
#                                   flags, info_text).size()
#
#         f.setPixelSize(14)
#         f.setBold(False)
#         fm = QFontMetrics(f)
#         boundRect = fm.boundingRect
#
#         text_rect = QRect(option.rect.left() + self.avatar_r*2 + self.padding_x + self.spacing,
#                                     0, option.rect.right() - self.padding_x*7 + self.getRightAdd(), 0) # FIXME self.padding_x*7....
#
#         total_height = 0
#         text_rect_width = text_rect.right() - text_rect.left() + self.getRightAdd()
#         huge_word_rect = None
#         part_I = ''
#         part_II = ''
#         for line in message.text.split('\n'):
#             words = line.split()
#             for word in words:
#                 word_w = fm.width(word)
#                 if word_w > text_rect_width:
#                     part_I, _, part_II = line.partition(word)
#                     line = part_I + part_II
#                     huge_word_rect = boundRect(text_rect, Qt.TextWrapAnywhere, word)
#                     total_height += huge_word_rect.height()
#             if len(line.strip()) > 0:
#                 line_rect = boundRect(text_rect, Qt.TextWordWrap, line)
#                 _count = 0
#                 if part_I:
#                     _count += 1
#                 if huge_word_rect is None:
#                     _count += 1
#                 total_height += line_rect.height()*_count
#
#         text_size = QSize(0, total_height)
#
#         info_quote_size = QSize(0, 0)
#         quote_size = QSize(0, 0)
#         file_size = QSize(0, 0)
#
#         # FIXME
#         if quote:
#             spacing_quote = self.spacing*2
#             info_quote_text = quote.getSenderName()
#             info_quote_size = boundRect(QRect(option.rect.left() + self.avatar_r*2 + self.padding_x + spacing_quote,
#                                               0, option.rect.right() - self.padding_x, 0),
#                                         flags, info_quote_text).size()
#             if quote.message != None and len(quote.message) > 0:
#                 quote_rect = boundRect(QRect(option.rect.left() + self.avatar_r*2 + self.padding_x + spacing_quote,
#                                              0, option.rect.right() - self.padding_x, 0),
#                                        flags, quote.message)
#
#                 total_height = 0
#                 quote_rect_width = quote_rect.right() - quote_rect.left()
#                 huge_word_rect = None
#                 for line in quote.message.split('\n'):
#                     words = line.split()
#                     for word in words:
#                         word_w = fm.width(word)
#                         if word_w > quote_rect_width:
#                             part_I, _, part_II = line.partition(word)
#                             line = part_I + part_II
#                             huge_word_rect = boundRect(quote_rect, Qt.TextWrapAnywhere, word)
#                             total_height += huge_word_rect.height()
#                     if len(line.strip()) > 0:
#                         line_rect = boundRect(quote_rect, Qt.TextWordWrap, line)
#                         if huge_word_rect is None or (quote_rect.right() - huge_word_rect.right()) > line_rect.width():
#                             total_height += line_rect.height()
#
#                 if len(message.text) > 0:
#                     total_height += 5
#                 quote_size = QSize(0, total_height)
#
#             elif quote.file != None and len(quote.file) > 1:
#                 quote_size = QSize(0, fm.height()*2) # FIXME
#
#         f_sum_h = 0
#         if has_file:
#             file_h = self.getFileHeight(message, has_file, fm)
#             file_size = QSize(0, file_h) # FIXME
#             title_h = 20
#             f_sum_h = file_h + title_h
#
#         sum_size = sum(map(lambda x: x.height(), [text_size, info_quote_size, quote_size, info_size, right_bottom_date_h]))
#         height = max(min_height, sum_size + 10) + 10 # FIXME
#         height = max(height, f_sum_h)
#         return QSize(option.rect.right(), height)
#
#     def getFileHeight(self, message, has_file, fm):
#         if has_file:
#             file_h = fm.height() * 2
#
#             _file_uuid = message.getFile()
#             icon = self.images.get(_file_uuid)
#             if icon:
#                 _w = self.listView.width() - 300
#                 if _w > 300:
#                     _w = 300
#                 isz = icon.actualSize(QSize(_w, self.listView.height()))
#                 return isz.height()
#             else:
#                 _fullpath = ChatApiCommon.getDownloadsFilePath(message.getFileName(), _file_uuid)
#                 file_exists = exists(_fullpath)
#
#                 # файл - изображение
#                 if file_exists:
#                     _lower_fullpath = _fullpath.lower()
#                     if _lower_fullpath.endswith('.jpg') or _lower_fullpath.endswith('.png'):
#                         icon = QIcon(_fullpath)
#                         self.images[_file_uuid] = icon
#                         _w = self.listView.width() - 300
#                         if _w > 300:
#                             _w = 300
#                         isz = icon.actualSize(QSize(_w, self.listView.height()))
#                         return isz.height()
#             return file_h
#         return 0
#
#     def editorEvent(self, event, model, option, index):
#         message = index.data()
#         font = option.font
#         font.setPixelSize(14)
#         fm = QFontMetrics(font)
#         boundRect = fm.boundingRect
#
#         last_message = None
#         if (index.row() - 1) >= 0:
#             messages = self.get_messages()
#             mess = messages[index.row() - 1]
#             if hasattr(mess, 'getSender'):
#                 last_message = mess
#
#         # FIXME simplify...
#         if event.type() == event.MouseButtonPress:
#             if isinstance(message, LoadMessagesButton):
#
#                 chat_api = ChatApi.instance()
#                 last_message = self.get_last_message()
#                 chat_api.getLastMessagesOnCurrentChat(last_message)
#
#             elif message.has_links:
#
#                 if last_message is None or last_message.getSender() != message.getSender():
#                     info_text = "{} {}".format(message.getSenderName(), message.getTimeString())
#                     info_rect = boundRect(QRect(option.rect.left() + self.avatar_r * 2 + self.padding_x + self.spacing,
#                                                 option.rect.top() + self.padding_y,
#                                                 option.rect.right() - self.padding_x + self.getRightAdd(), option.rect.top() + self.padding_y),
#                                           Qt.TextWrapAnywhere, info_text)
#                 else:
#                     info_rect = QRect(QRect(QPoint(option.rect.left() + self.padding_x, option.rect.top() + self.padding_y),
#                                    QPoint(option.rect.right() - self.padding_x + self.getRightAdd(), option.rect.top() + self.padding_y)))
#                 if message.quote:
#                     # проверка пересылаемого текста на ссылки
#                     spacing_quote = self.spacing*2
#                     info_quote_text = message.quote.getSenderName()
#                     info_quote_rect = boundRect(
#                         QRect(option.rect.left() + self.avatar_r * 2 + self.padding_x + spacing_quote,
#                               info_rect.bottom(), option.rect.right() - self.padding_x + self.getRightAdd(), info_rect.bottom()),
#                         Qt.TextWrapAnywhere, info_quote_text)
#                     quote_rect = boundRect(QRect(
#                         QPoint(option.rect.left() + self.avatar_r * 2 + self.padding_x + spacing_quote, info_quote_rect.bottom()),
#                         QPoint(option.rect.right() - self.padding_x + self.getRightAdd(), info_quote_rect.bottom())),
#                                            Qt.TextWrapAnywhere, message.quote.message)
#                     for is_new_line, r, char_seq, is_selection, is_link in self.genRectText(font, message.quote.message, quote_rect, message):
#                         if is_link:
#                             if r.contains(event.pos()):
#                                 webbrowser.open(is_link, new=0, autoraise=True)
#                                 break
#
#                     # проверка дополнительного текста на ссылки
#                     rect = QRect(QPoint(option.rect.left() + self.avatar_r * 2 + self.padding_x + self.spacing, quote_rect.bottom()),
#                                  QPoint(option.rect.right() - self.padding_x + self.getRightAdd(), quote_rect.bottom()))
#
#                     for is_new_line, r, char_seq, is_selection, is_link in self.genRectText(font, message.text, rect, message):
#                         if is_link:
#                             if r.contains(event.pos()):
#                                 webbrowser.open(is_link, new=0, autoraise=True)
#                                 break
#
#                 else:
#                     rect = QRect(QPoint(option.rect.left() + self.avatar_r * 2 + self.padding_x + self.spacing, info_rect.bottom()),
#                                  QPoint(option.rect.right() - self.padding_x + self.getRightAdd(), info_rect.bottom()))
#
#                     for is_new_line, r, char_seq, is_selection, is_link in self.genRectText(font, message.text, rect, message):
#                         if is_link:
#                             if r.contains(event.pos()):
#                                 webbrowser.open(is_link, new=0, autoraise=True)
#                                 break
#
#         return super(MessagesDictDelegate, self).editorEvent(event, model, option, index)
#
#     def get_messages(self):
#         # if self.clear:
#         #     return []
#         if not ChatApi.instance().current_chat_messages:
#             return []
#         messages = sorted(ChatApi.instance().current_chat_messages.values(), key=lambda mess: int(mess.mes_id))
#         if len(messages) >= 20:
#             messages.insert(0, LoadMessagesButton('load more messages...'))
#         return messages
#
#     def get_messages_dict(self):
#         d = {}
#         for m in self.get_messages():
#             if hasattr(m, 'mes_id'):
#                 d[m.mes_id] = m
#         return d
#
#     def get_last_message(self):
#         return min(map(int, ChatApi.instance().current_chat_messages.keys()))
#
#     def setReadedForMessage(self, messages):
#         mData = self.get_messages_dict()
#         for id in messages:
#             if id in mData:
#                 mData.get(id).setDelivered(True)
#
#     def set_clear(self, value):
#         self.clear = value
#
#
# class MessagesDictModel(QAbstractListModel):
#
#     delegate = None
#     withScrollToBottom = False
#     updateMeSignal = pyqtSignal()
#     updateMeTimer = None
#
#     def __init__(self, delegate, withScrollToBottom):
#         super().__init__()
#         self.delegate = delegate
#         self.withScrollToBottom = withScrollToBottom
#         self.updateMeSignal.connect(self.updateMeSlot)
#
#     def rowCount(self, parent=None):
#         m_count = len(self.delegate.get_messages())
#         return m_count
#
#     def data(self, index, role=None):
#         messages = self.delegate.get_messages()
#         return messages[index.row()]
#     #
#     # def flags(self, index):
#     #     return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
#
#     def updateMe(self, clear=False, withScrollToBottom=False):
#         self.delegate.set_clear(clear)
#         self.delegate.listView.clearSelectionItems(clear)
#         self.withScrollToBottom = withScrollToBottom
#         if self.updateMeTimer:
#             return
#         self.updateMeTimer = Timer(0.1, self.updateMeStart)
#         self.updateMeTimer.start()
#
#     def updateMeStart(self):
#         self.updateMeSignal.emit()
#         self.updateMeTimer = None
#
#     def updateMeSlot(self):
#         count = self.rowCount()
#         temp_indx = self.delegate.listView.selectedIndexes()
#         self.beginResetModel()
#         self.endResetModel()
#         # FIXME hack...
#         item_selection = QItemSelection()
#         for i in temp_indx:
#             item_selection.select(i, i)
#         self.delegate.listView.selectionModel().select(item_selection, QItemSelectionModel.Select)
#
#         if self.withScrollToBottom:
#             self.withScrollToBottom = False
#             self.delegate.listView.messagesScrollToBottom()
#         else:
#             _getting_last_messages = ChatApi.instance()._getting_last_messages
#             if _getting_last_messages:
#                 last_message = _getting_last_messages['last_message']
#                 messages = self.delegate.get_messages()
#                 for i, m in enumerate(messages):
#                     if hasattr(m, 'mes_id') and m.mes_id == last_message:
#                         self.delegate.listView.scrollToIndex(i)
#                         return
#
#
# class LoadMessagesButton:
#
#     text = "Load more messages"
#
#     def __init__(self, text=None):
#         if text is not None:
#             self.text = text
#
