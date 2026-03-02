import re
from datetime import datetime

from .QuoteInfo import QuoteInfo
from ..chat_api.api_object import ApiObject


class Message(ApiObject):

    text = ""
    _text = ""
    sender_id = None
    _mes_id = None
    chat_id = None

    quote:QuoteInfo = None
    file = None
    file_size = None

    _time = None
    is_html = False
    has_links = False
    _links = []
    _delivered = True # delivered?

    api_type = None
    api_kwargs = None

    _selected_text = None
    prev_id = 0
    favorite = 0
    got_time = 0

    @property
    def id(self):
        return self.mes_id

    @property
    def selected_text(self):
        return self._selected_text

    def set_selected_text(self, val):
        if self._selected_text != val:
            self._selected_text = val

    def __init__(self, text, mes_id=None):
        if text != None:
            self.set_text(text)
        self.mes_id = mes_id

    @property
    def mes_id(self):
        return self._mes_id

    @mes_id.setter
    def mes_id(self, val):
        if val is None:
            self._mes_id = val
        else:
            self._mes_id = int(val)

    def __str__(self):
        return '(mes:{})'.format(self.mes_id)

    def __repr__(self):
        return self.__str__()

    @property
    def file_name(self): # FIXME it is cause we have file name in message text or in quote
        return self.getFileName()

    @property
    def sender(self):
        return self.chat_api.getUser(self.sender_id)

    @classmethod
    def fromJSONObject(cls, json):
        message = Message(None)
        message.getTextFromJSONObject(json)
        message.sender_id = cls.getAttrFromJSONObject(json, "sender", "-1")
        time = cls.getFloatFromJSONObject(json, "ts", 0) or cls.getAttrFromJSONObject(json, "date", "")
        message.setTime(time)
        message.chat_id = cls.getIntFromJSONObject(json, "chat_id", -1)
        message.file = cls.getAttrFromJSONObject(json, "file", None)
        message.file_size = cls.getAttrFromJSONObject(json, "file_size", None)
        message._delivered = cls.getBoolFromJSONObject(json, "delivered", False)
        message.prev_id = cls.getIntFromJSONObject(json, "prev_id", 0)
        return message

    def setTime(self, time):
        if type(time) == str:
            last_time = time.split('.')[0]
            if "T" in time:
                time = datetime.strptime(last_time, "%Y-%m-%dT%H:%M:%S")
            else:
                time = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
        elif type(time) == float:
            time = datetime.fromtimestamp(time)
        self._time = time

    @property
    def datetime(self):
        return self._time

    @property
    def timestamp(self):
        return self._time.timestamp()

    @timestamp.setter
    def timestamp(self, val):
        self._time = datetime.fromtimestamp(val)

    def setDelivered(self, delivered): # FIXME
        self._delivered = delivered

    def getDelivered(self):
        return self._delivered

    @property
    def delivered(self):
        return 1 if self._delivered else 0

    @delivered.setter
    def delivered(self, val):
        self._delivered = True if val else False

    def getSenderName(self):
        sender = self.getSender()
        if sender != None:
            return sender.login
        return None

    def getLinks(self):
        return self._links

    def getFile(self):
        _file = self.file
        if self.quote != None and self.quote.file != None and len(self.quote.file) > 0 and self.quote.file != "0":
            _file = self.quote.file
        return _file

    def getFileName(self):
        _file = self.text # FIXME
        if self.quote != None and self.quote.fileName != None and len(self.quote.fileName) > 0 and self.quote.fileName != "0":
            _file = self.quote.fileName
        return _file

    @property
    def has_file(self):
        file = self.file
        return file is not None and len(file) > 1

    def getSender(self):
        user = self.chat_api.getUser(self.sender_id)
        return user

    def isMyMessage(self):
        return self.sender_id == self.chat_api.getUser(self.sender_id)

    def getFileSize(self):
        file_size = self.file_size
        if self.quote != None and self.quote.fileSize != None and self.quote.fileSize not in (0, '0'):
            file_size = self.quote.fileSize
        return self.fileSizeToStringFromRaw(file_size)

    def getFileSizeDouble(self):
        return self.fileSizeToDoubleFromRaw(self.file_size)

    @classmethod
    def fileSizeToStringFromRaw(cls, rawSize):
        return cls.fileSizeToString(cls.fileSizeToDoubleFromRaw(rawSize))

    @classmethod
    def fileSizeToDoubleFromRaw(cls, rawSize):
        if (type(rawSize) is str and len(rawSize) > 0 and rawSize != "0") or \
                (type(rawSize) in (int, float)):
            return float(rawSize)
        else:
            return 0

    @classmethod
    def fileSizeToString(cls, value):
        if value != 0:
            tp = "bytes"
            if value >= 1024:
                value = value / 1024
                tp = "Kb"
            if value >= 1024:
                value = value / 1024
                tp = "Mb"
            if value >= 1024:
                value = value / 1024
                tp = "Gb"
            return str(int(round(value))) + " " + tp
        return "0 Kb"

    def getTimeString(self):
        return self.getTimeStringBase(True)

    def getTimeStringShort(self):
        return self.getTimeStringBase(False)

    def getTimeStringBase(self, full):
        #Calendar cal = Calendar.getInstance()
        #TimeZone tz = cal.getTimeZone()
        localTime = "--:--"
        if self._time != None:
            if full:
                format = "%d.%m.%Y %H:%M" # :ss
            else:
                format = "%d.%m.%Y"

            today = datetime.now()
            year_today = today.year
            month_today = today.month
            day_today = today.day

            timeday = self._time #datetime.fromtimestamp(self._time)
            year = timeday.year
            month = timeday.month
            day = timeday.day
            if year == year_today and month == month_today and day == day_today:
                format = "%H:%M" # :ss
            localTime = timeday.strftime(format)
        return localTime

    def getTimestamp(self):
        if self._time == None:
            return 0.0
        return float(self._time.timestamp())

    def set_text(self, _text):
        self._text = _text
        _text = _text.rstrip().replace('\t', '    ')

        if _text.startswith('#INPUT_CALL:'):
            _from = _text[len('#INPUT_CALL:'):]
            self.api_type = 'INPUT_CALL'
            self.api_kwargs = {'from': _from}

        self.is_html = self.is_text_html(_text)
        self.has_links = self.has_text_links(_text)

        self._links = []

        while "[QUOTE" in _text:
            start_tag = "[QUOTE"
            start_tag_fin = "]"
            end_tag = "[/QUOTE]"

            start = _text.find(start_tag)
            stop = _text.find(start_tag_fin, start)

            before = _text[0 : start]
            paramsString = _text[start + len(start_tag) : stop]

            start = _text.rfind(end_tag)
            inner = _text[stop + len(start_tag_fin) : start]
            after = _text[start + len(end_tag) : len(_text)]

            # FIXME regexp
            inner, _links = self.extract_colors_and_refs(inner)
            self._links.extend(_links)

            qi = QuoteInfo.make(paramsString, inner)
            _text = before + after
            self.quote = qi

        _text, _links = self.extract_colors_and_refs(_text)
        self._links.extend(_links)

        if len(self._links) > 0 and not self.has_links:
            self.has_links = True

        self.text = _text

    @property
    def text_full(self):
        return self._text

    @text_full.setter
    def text_full(self, val):
        self._text = val

    def get_text(self, maxlines=100):
        return self._prepare_text(self.text, maxlines)

    def get_quote_text(self, maxlines=100):
        if not self.quote or not self.quote.message:
            return
        return self._prepare_text(self.quote.message, maxlines)

    def _prepare_text(self, text, maxlines):
        lines = text.replace('\t', '    ').split('\n')
        text = '\n'.join(lines[:maxlines])
        return text

    def getTextFromJSONObject(self, json):
        _text = self.getAttrFromJSONObject(json, "message", "")
        self.set_text(_text)

    # def getTimeString(self):
    #     if not self.time:
    #         return None
    #     now = datetime.now()
    #     if self.time.year == now.year and self.time.month == now.month and self.time.day == now.day:
    #         return self.time.strftime("%H:%M")
    #     else:
    #         return self.time.strftime("%Y-%m-%d")

    @staticmethod
    def is_text_html(_text):
        return "[color=" in _text or "[ref=" in _text or "</a>" in _text

    @staticmethod
    def has_text_links(_text):
        return "[ref=" in _text or "<a href=" in _text or "http://" in _text or "https://" in _text

    @classmethod
    def extract_colors_and_refs(cls, _text):
        _text = cls.extract_colors(_text)
        _text, _refs = cls.extract_refs(_text)
        return _text, _refs

    @classmethod
    def extract_colors(cls, _text):
        try:
            while "[color=" in _text:
                _text = cls.extract_kv_link(_text, "[color=", "]", "[/color]", "{before}{inner}{after}")
        except Exception as e:
            pass
        return _text

    @classmethod
    def extract_refs(cls, _text):
        _links = []
        try:
            while "[ref=" in _text:
                #_text = cls.extract_kv_link(_text, "[ref=", "]", "[/ref]", "{before}<a href='{inner}'>{inner}</a>{after}")
                _text = cls.extract_kv_link(_text, "[ref=", "]", "[/ref]", "{before}{inner}{after}", _links)
        except Exception as e:
            pass

        try:
            while "<a href=" in _text:
                _text = cls.extract_kv_link(_text, "<a href=", ">", "</a>", "{before}{inner}{after}", _links)
        except Exception as e:
            pass

        for a in filter(None, re.split("[ \n]+", _text)):
            if cls.maybe_link(a) and a not in _links:
                _links.append(a)

        return _text, _links

    @classmethod
    def maybe_link(cls, a):
        return cls.maybe_url_link(a) or cls.maybe_dir_link(a)

    @classmethod
    def maybe_url_link(cls, a):
        return a.startswith("http://") or a.startswith("https://")

    @classmethod
    def maybe_dir_link(cls, a):
        return len(a) >= 2 and a[1] == ":"

    @staticmethod
    def extract_kv_link(_text, start_tag, start_tag_fin, end_tag, format, _links=None):

        start = _text.find(start_tag)
        stop = _text.find(start_tag_fin, start)

        before = _text[0 : start]

        start = _text.find(end_tag, stop)

        inner = _text[stop + len(start_tag_fin) : start]
        after = _text[start + len(end_tag) : len(_text)]

        # FIXME
        if _links is not None:
            _links.append(inner)

        return format.replace("{before}", before).replace("{inner}", inner).replace("{after}", after)

    @staticmethod
    def getAttrFromJSONObject(json, attrName, defaultAttr):
        attr = defaultAttr
        if attrName in json:
            attr = json[attrName]
        return attr

    @staticmethod
    def getFloatFromJSONObject(json, attrName, defaultAttr):
        attr = defaultAttr
        if attrName in json:
            attr = float(json[attrName])
        return attr

    @staticmethod
    def getIntFromJSONObject(json, attrName, defaultAttr):
        attr = defaultAttr
        if attrName in json:
            attr = int(json[attrName])
        return attr

    @staticmethod
    def getBoolFromJSONObject(json, attrName, defaultAttr):
        attr = 0
        bool_attr = defaultAttr
        attr = defaultAttr
        if attrName in json:
            attr = json.get(attrName, 0)
            bool_attr = True if attr else False
        return bool_attr
