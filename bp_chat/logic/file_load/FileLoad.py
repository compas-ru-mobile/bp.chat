
from os.path import join, dirname, exists
from os import makedirs
import requests

from .FileLoadBase import FileLoadBase
from ..chat_api import ChatApiCommon


class FileLoad(FileLoadBase):

    file = None
    FILE_LOAD_TYPE = FileLoadBase.FILE_DOWNLOAD

    def download(self, fileId, fileName):

        self.file = fileId
        self.fileName = fileName

        file = self.doDownload()

        if self.m_error != None:
            return

        fileState = "FULL"
        if self.int_error == self.NOT_FULL_FILE:
            fileState = "NOT FULL"
        elif self.int_error == self.CANCELLED_BY_USER:
            fileState = "CANCELLED"

        chatApi = self.chat_api
        if file != None:
            if chatApi.callbacks != None:
                chatApi.callbacks.messagesUpdateCallback(False) # FIXME -- update --
        elif self.data != None:
            chatApi.updateAvatar(self.file, self.data, source='FileLoad')

    def doDownload(self):
        self.initProgress(self.FILE_DOWNLOAD)

        chatApi = self.chat_api
        serverAddress = chatApi.getCurrentServerAddress()

        http = "https"
        if ChatApiCommon.isUrlHttp(serverAddress):
            http = "http"

        url = http + "://" + serverAddress + "/file/?version=" + chatApi.CLIENT_API_VERSION + "&uuid=" + ChatApiCommon.getDeviceId() + "&file_id=" + self.file + "&user=" + str(chatApi.getCurrentUserId())

        _file = None
        if len(self.fileName) == 0:
            self.data = ChatApiCommon.loadAvatarFromAppDir(self.file)
            if self.data != None:
                return None
        else:
            #_file_name = join(ChatApiCommon.getDownloadsDirectoryPath(), self.fileName)
            _file_name = ChatApiCommon.getDownloadsFilePath(self.fileName, self.file)
            dir_path = dirname(_file_name)
            if not exists(dir_path):
                makedirs(dir_path)
            _file = open(_file_name, 'wb')

        if True:

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": str(chatApi.user_id) + '=' + chatApi.user_token
            }
            r = requests.get(url, stream=True, headers=headers, verify=False)  # FIXME verify in future maybe...

            if _file != None:
                fos = _file
            else:
                fos = None

            totalSize = int(r.headers['Content-length'])
            downloadedSize = 0

            chatApi.fileLoadProgress(self.file, 0, True)
            _progress = 0

            for ch_i, chunk in enumerate(r.iter_content(chunk_size=8192)):

                if chunk != None:
                    bufferLenght = len(chunk)
                    fos.write(chunk)
                else:
                    bufferLenght = 0

                downloadedSize += bufferLenght

                _progress = int(downloadedSize * 100.0 / totalSize)

                self.updateProgress(_progress, self.file)

                if self.infoFromJob.isCancelled():
                    self.cancelled = True
                    break

            self.finishProgress(totalSize == downloadedSize, self.file)
            self.s_error = str(downloadedSize) + " / " + str(totalSize)

            if _file != None:
                fos.close()
                return _file
            else:
                data = fos.toByteArray()
                ChatApiCommon.saveAvatarToAppDir(self.file, data)
                return None

        return None
