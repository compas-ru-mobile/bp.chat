
from datetime import datetime

from ..chat_api.ChatApiCommon import CHAT_API_ENUMS, ProgressNotify
from ..chat_api.api_object import ApiObject


class InfoFromJob:

    def isCancelled(self):
        raise NotImplementedError


class FileLoadBase(ApiObject):

    NOT_FULL_FILE = 1
    CANCELLED_BY_USER = 2

    FILE_DOWNLOAD = CHAT_API_ENUMS.FILE_DOWNLOAD
    FILE_DOWNLOAD_AVATAR = CHAT_API_ENUMS.FILE_DOWNLOAD_AVATAR
    FILE_UPLOAD = CHAT_API_ENUMS.FILE_UPLOAD

    FILE_LOAD_TYPE = None

    fileName = None
    data = None
    m_error = None
    int_error = 0
    s_error = ""
    progress = -1
    progress_last_visible = -1
    lastSendProgress = None

    infoFromJob = None
    progressNoti = None
    cancelled = False


    def setInfoFromJob(self, infoFromJob):
        self.infoFromJob = infoFromJob

    def download(self, fileId, fileName):
        pass

    def initProgress(self, type):
        self.progress = 0
        self.progress_last_visible = -1
        self.lastSendProgress = None

        self.progressNoti = ProgressNotify(self.fileName, type)
        self.progressNoti.updateProgress(0)

        self.cancelled = False

    def updateProgress(self, _progress, fileId):
        currentTime = datetime.now()
        d = -1
        if self.lastSendProgress != None:
            d = (currentTime - self.lastSendProgress).total_seconds()
        if d < 0 or d >= 1:
            self.progress_last_visible = _progress
            self.progressNoti.updateProgress(_progress)

            self.lastSendProgress = currentTime
            if fileId != None:
                self.chat_api.fileLoadProgress(fileId, _progress, self.FILE_LOAD_TYPE == FileLoadBase.FILE_DOWNLOAD)

    def finishProgress(self, success, fileId):
        if success:
            self.progressNoti.finish(True, self.cancelled)
            if fileId != None:
                self.chat_api.fileLoadProgress(fileId, 100, self.FILE_LOAD_TYPE == FileLoadBase.FILE_DOWNLOAD)
        else:
            self.int_error = self.NOT_FULL_FILE
            if self.cancelled:
                self.int_error = self.CANCELLED_BY_USER
            self.progressNoti.finish(False, self.cancelled)