
from os.path import basename
import requests
import hashlib
from datetime import datetime

from .FileLoadBase import FileLoadBase
from ..chat_api import ChatApiCommon
from ..chat_api.api_object import ApiObject


class FileUpload(FileLoadBase, ApiObject):

    FILE_LOAD_TYPE = FileLoadBase.FILE_UPLOAD

    fileSize = None
    chat_id = None
    fullFilename = None
    uriString = None
    user_avatar = None

    maxBufferSize = 1 * 1024 * 1024

    def __init__(self, fullFilename, fileSize, chat_id, uriString, user_avatar):
        self.fileSize = fileSize
        self.chat_id = chat_id
        self.fullFilename = fullFilename
        self.uriString = uriString
        self.user_avatar = user_avatar

    def download(self, fileId, fileName):
        self.doDownload(fileId, fileName)
        self.chat_api.setCreatedFile(None)

    def doDownload(self, fileId, fileName):
        self.initProgress(self.FILE_UPLOAD)

        serverAddress = self.chat_api.getCurrentServerAddress()

        _file = None #// = this.file;
        uri = None

        if self.uriString != None:
            uri = self.uriString
            _file = None
        else:
            _file = self.chat_api.createdFile
            fileName = basename(_file.name)
            self.fileSize = str(_file.size())

        filename_encoded = fileName # FIXME

        attrs = [
                "version=" + self.chat_api.CLIENT_API_VERSION,
                "uuid=" + ChatApiCommon.getDeviceId(),
                "file_size=" + str(self.fileSize),
                "postfix=" + str(self.make_uuid()),
                "file_name=" + filename_encoded,

        ]
        if self.user_avatar == None:
            attrs += [
                "user=" + str(self.chat_api.getCurrentUserId()),
                "chat_id=" + str(self.chat_id)
            ]
        else:
            attrs += [
                "user=" + str(self.user_avatar),
                "is_avatar=true"
            ]

        is_stream = self.is_stream()

        str_attrs = '&'.join(attrs)

        http = "https"
        if ChatApiCommon.isUrlHttp(serverAddress):
            http = "http"

        if is_stream:
            url = http + "://" + serverAddress + "/file/stream/?" + str_attrs
        else:
            url = http + "://" + serverAddress + "/file/?" + str_attrs

        attrs_s = ""
        for s in attrs:
            attrs_s += s + " "

        headers = {
            "Content-Type": "application/octet-stream",
            "Content-lenght": str(self.fileSize),
            "Accept": "application/json",
            "Authorization": str(self.chat_api.user_id) + '=' + self.chat_api.user_token
        }
        self._file = _file
        self.uri = uri

        if is_stream:
            data = self
        else:
            data = self.make_fileInputStream().read()

        self.r = requests.post(url, stream=is_stream, headers=headers, verify=False, data=data) # FIXME verify in future maybe...

        if not is_stream:
            self.finishProgress(True, None)

    def is_stream(self):
        return True

    def make_fileInputStream(self):
        if self._file != None:
            return self._file
        else:
            return ChatApiCommon.openInputStream_from_ContentResolver(self.uri)

    def __iter__(self):
        sentBytes = 0

        fileInputStream = self.make_fileInputStream()
        bytesAvailable = int(self.fileSize)
        allFileSize = int(self.fileSize)

        bufferSize = min(bytesAvailable, self.maxBufferSize)

        _progress = 0

        totalSize = int(self.fileSize)

        #// Send file data
        buffer = fileInputStream.read(bufferSize)
        bytesRead = len(buffer) if buffer else 0
        while bytesRead and bytesRead > 0:
            if self.infoFromJob.isCancelled():
                self.cancelled = True
                break

            yield buffer

            sentBytes += bufferSize

            _progress = int(sentBytes * 100.0 / totalSize)

            self.updateProgress(_progress, None)

            bytesAvailable = totalSize - sentBytes
            if bytesAvailable < 0:
                break

            bufferSize = min(bytesAvailable, self.maxBufferSize)
            buffer = fileInputStream.read(bufferSize)
            bytesRead = len(buffer) if buffer else 0

        self.finishProgress(allFileSize == sentBytes, None)

    def __len__(self):
        return self.fileSize

    def make_uuid(self):
        m = hashlib.md5()
        datetime.now()
        m.update(str(datetime.now()).encode('utf-8'))
        return m.hexdigest()