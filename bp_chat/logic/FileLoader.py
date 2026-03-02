
from os.path import join
from concurrent.futures import ThreadPoolExecutor
import requests

from .chat_api.api_object import ApiObject
from .chat_api import ChatApiCommon


class FileLoader(ApiObject):

    __executor = None

    NOT_FULL_FILE = 1
    CANCELLED_BY_USER = 2

    file = None
    fileName = None
    data = None
    m_error = None
    int_error = 0
    s_error = ""
    progress = -1
    progress_last_visible = -1

    @staticmethod
    def executor():
        if not FileLoader.__executor:
            FileLoader.__executor = ThreadPoolExecutor()
        return FileLoader.__executor

    def __init__(self, file, fileName):
        self.file = file
        self.fileName = fileName

    def executeOnExecutor(self):
        self.executor().submit(self.execute)

    def execute(self):
        fi = self.doInBackground()
        self.onPostExecute(fi)

    @ChatApiCommon.tryable
    def doInBackground(self, *params):
        self.progress = 0
        self.progress_last_visible = -1

        chatApi = self.chat_api
        serverAddress = chatApi.getCurrentServerAddress()

        http = "https"
        if ChatApiCommon.isUrlHttp(serverAddress):
            http = "http"

        url = http + "://" + serverAddress + "/file/?version="+ chatApi.CLIENT_API_VERSION +"&uuid=" + ChatApiCommon.getDeviceId() + "&file_id=" + self.file + "&user=" + str(chatApi.getCurrentUserId())

        _file = None
        if not self.fileName or len(self.fileName) == 0:
            data = ChatApiCommon.loadAvatarFromAppDir(self.file)
            if data != None:
                self.data = data
                return None
        else:
            _file = open(join(ChatApiCommon.getDownloadsDir(), self.fileName), 'wb')

        fileName = "temp_file"

        if True:

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": str(chatApi.user_id) + '=' + chatApi.user_token
            }
            r = requests.get(url, stream=True, headers=headers, verify=False) # FIXME verify in future maybe...

            PROGRESS_MAX = 100

            data = b''
            for ch_i, chunk in enumerate(r.iter_content(chunk_size=8192)):
                #fd.write(chunk)
                data += chunk

            self.data = data

            if _file != None:
                pass # FIXME
                # fos.close();
                # inputStream.close();
                # return _file;
            else:
                ChatApiCommon.saveAvatarToAppDir(self.file, data)
                self.data = ChatApiCommon.loadAvatarFromAppDir(self.file)
                return None

        return None

    @ChatApiCommon.tryable
    def onPostExecute(self, file):
        if self.m_error != None:
            #m_error.printStackTrace() FIXME
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
            chatApi.updateAvatar(self.file, self.data, source='FileLoader')

        else:
            pass
