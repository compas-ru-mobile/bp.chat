
from concurrent.futures import ThreadPoolExecutor

from .FileLoadBase import FileLoadBase, InfoFromJob
from .FileUpload import FileUpload
from .FileLoad import FileLoad
from ..chat_api.api_object import ApiObject
from ..chat_api.ChatApiCommon import tryable


class FileDownloadJob(ApiObject):

    TAG = "job_filedownload_tag"

    #// For download:
    FILE_ID = "file_id"
    FILE_NAME = "file_name"
    FILE_SIZE = "file_size"
    FILE_URI = "file_uri"

    #// For upload:
    FULL_FILE_NAME = "full_file_name"
    CURRENT_CHAT_ID = "current_chat_id"
    USER_AVATAR = "user_avatar"
    TYPE = "type"

    jobId = -1
    maxJobId = 0
    _cancelled = set()
    __executor = None

    # NotificationManager mNotifyManager;
    # NotificationCompat.Builder mBuilder;

    @classmethod
    def executor(cls):
        if not cls.__executor:
            cls.__executor = ThreadPoolExecutor(max_workers=1)
        return cls.__executor


    def __init__(self, extras):
        self._extras = extras

    def executeOnExecutor(self):
        self.executor().submit(self.execute)

    def execute(self):
        self.onRunJob(self._extras)

    @tryable
    def onRunJob(self, extras):
        #// run your job here
        self.jobId = FileDownloadJob.maxJobId + 1 #extras.get('id')
        FileDownloadJob.maxJobId = self.jobId

        #PersistableBundleCompat extras = params.getExtras();
        type = extras.get(self.TYPE, 0)

        typeString = "DOWNLOAD"
        if type == FileLoadBase.FILE_UPLOAD:
            typeString = "UPLOAD"

        chatApi = self.chat_api
        chatApi.setJobFileDownload(self.jobId)
        chatApi.setJobFileDownloadType(type)
        chatApi.savePrefs()

        job = self

        load = None #//new FileLoad();
        if type == FileLoadBase.FILE_DOWNLOAD:
            load = FileLoad()
        elif type == FileLoadBase.FILE_UPLOAD:
            load = FileUpload(
                extras.get(self.FULL_FILE_NAME, None),
                extras.get(self.FILE_SIZE, None),
                extras.get(self.CURRENT_CHAT_ID, -1),
                extras.get(self.FILE_URI, None),
                extras.get(self.USER_AVATAR, None)
            )

        if load != None:

            class _InfoFromJob(InfoFromJob):
                def isCancelled(self):
                    return job.isCanceled()

            load.setInfoFromJob(_InfoFromJob())
            load.download(
                    extras.get(self.FILE_ID, ""),
                    extras.get(self.FILE_NAME, "")
            )

        if self.jobId in self._cancelled:
            self._cancelled.remove(self.jobId)

        chatApi.setJobFileDownload(-1)
        chatApi.savePrefs()

        return True

    def isCanceled(self):
        return self.jobId in self._cancelled

    @classmethod
    def runJobDownload(cls, file, fileName):
        extras = {}
        extras[cls.FILE_ID] = file
        extras[cls.FILE_NAME] = fileName
        extras[cls.TYPE] = FileLoadBase.FILE_DOWNLOAD
        cls.__runJobImmediately(extras)

    @classmethod
    def runJobUploadByCreatedFile(cls, current_chat_id, fileSize, fileName):
        extras = {}
        extras[cls.FILE_NAME] = fileName
        extras[cls.CURRENT_CHAT_ID] = current_chat_id
        extras[cls.FILE_SIZE] = str(fileSize)
        extras[cls.TYPE] = FileLoadBase.FILE_UPLOAD
        cls.__runJobImmediately(extras)

    @classmethod
    def runJobUploadByUri(cls, uriString, fileName, fileSize, current_chat_id, user_avatar):
        extras = {}
        extras[cls.FILE_NAME] = fileName
        extras[cls.FILE_SIZE] = fileSize
        extras[cls.FILE_URI] = uriString
        extras[cls.CURRENT_CHAT_ID] = current_chat_id
        extras[cls.TYPE] = FileLoadBase.FILE_UPLOAD
        extras[cls.USER_AVATAR] = user_avatar
        cls.__runJobImmediately(extras)

    @classmethod
    def __runJobImmediately(cls, extras):
        FileDownloadJob(extras).executeOnExecutor()
        # int _jobId = new JobRequest.Builder(FileDownloadJob.TAG)
        #         .addExtras(extras)
        #         .startNow()
        #         .build()
        #         .schedule();

    @classmethod
    def cancelJob(cls):
        chatApi = cls.get_chat_api()
        if chatApi.jobFileDownload != -1:

            #JobManager.instance().cancel(chatApi.jobFileDownload)
            # FIXME !!! cancel by job id !!!
            cls._cancelled.add(chatApi.jobFileDownload)

            chatApi.jobFileDownload = -1
            chatApi.savePrefs()
            return True

        return False