from ..chat_api.api_object import ApiObject


class QuoteInfo(ApiObject):

    message = None
    sender = None
    file = None
    fileName = None
    fileSize = None

    def __init__(self, message, sender, fileName, fileSize, file):
        self.message = message
        self.sender = sender
        sender.quote = self
        self.fileName = fileName
        self.fileSize = fileSize
        self.file = file

    def toHtmlString(self):
        return "<b>" + self.message + "</b>"

    @classmethod
    def make(cls, paramsString, inner):

        sender_name = cls.excludeParam(paramsString, "sender")
        sender_id = cls.excludeParam(paramsString, "sender_id")
        fileName = cls.excludeParam(paramsString, "file_name")
        fileSize = cls.excludeParam(paramsString, "file_size")
        file = cls.excludeParam(paramsString, "file")

        sz = 0
        if fileSize and len(fileSize) > 0:
            try:
                sz = float(fileSize)
            except Exception as e:
                pass

        return QuoteInfo(inner, QuoteSender(sender_id, sender_name), fileName, sz, file)

    @staticmethod
    def excludeParam(text, paramName):
        param = None
        paramName += "="
        if paramName in text:
            start = text.find(paramName)
            end = text.find(";", start)
            if end < 0:
                end = len(text)
            param = text[start + len(paramName) : end]
        return param

    def getSenderName(self):
        return self.sender.getName()

    def findUserInUsers(self, id):
        return self.chat_api.getUser(id)


class QuoteSender:

    name = None
    id = None
    quote = None

    def __init__(self, sender_id, sender_name):
        self.id = sender_id
        self.name = sender_name

    def getName(self, full=True):
        if self.id == None: # FIXME hack for old format...
            self.id = self.name
        if self.id != None:
            sender = self.quote.findUserInUsers(self.id)
            if sender != None:
                return sender.name
        return self.name