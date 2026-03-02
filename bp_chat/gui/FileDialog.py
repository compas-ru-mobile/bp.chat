
import subprocess
from os.path import exists, basename, getsize

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices

from .ui.UiFileDialog import Ui_FileDialog

from bp_chat.logic.common.app_common import APP_TITLE
from bp_chat.logic.chat_api.ChatApi import ChatApi

from bp_chat.core.local_db_files import getDownloadsFilePath, LocalDbFilesMap
from .common.langs import tr_w


class FileDialog(QDialog, Ui_FileDialog):

    file_path = None
    file_size = None
    file_uid = None

    @classmethod
    def by_file_id(cls, parent, file_uid, filter_ends=None):
        filename = LocalDbFilesMap.get(None, file_uid)
        file_path = getDownloadsFilePath(filename, file_uid)
        file_size = getsize(file_path) if exists(file_path) else 0

        if filter_ends:
            filename_lower = filename.lower()
            for a in filter_ends:
                if filename_lower.endswith(a.lower()):
                    return

        _dialog = FileDialog(parent, file_path, file_size, file_uid)
        _dialog.exec()


    def __init__(self, main_widget=None, file_path=None, file_size=None, file_uid=None, flags=Qt.Window, *args, **kwargs):
        self.mw = main_widget

        if file_uid != None and file_path == file_size == None:
            filename = LocalDbFilesMap.get(None, file_uid)
            file_path = getDownloadsFilePath(filename, file_uid)
            file_size = getsize(file_path) if exists(file_path) else 0

        self.file_path = file_path
        self.file_size = file_size
        self.file_uid = file_uid

        super().__init__(main_widget)

        self.setupUi(self)
        self.retranslateUi(self)

        self.prepareView()
        self.connectSignals()

    def prepareView(self):
        flags = self.windowFlags()
        flags = int(flags)
        flags &= ~Qt.WindowContextHelpButtonHint
        flags = Qt.WindowFlags(flags)
        self.setWindowFlags(flags)
        self.setWindowTitle(APP_TITLE + " - File")

        tr_w(self.label)
        tr_w(self.openFileButton)
        tr_w(self.openInFolderButton)
        tr_w(self.reloadButton)
        tr_w(self.closeButton)

        text = '{}, \nsize: {}'.format(self.file_path, self.file_size)
        self.fileInfoLabel.setText(text)

        self.reloadButton.setVisible(not (self.file_path and not exists(self.file_path)) and bool(self.file_uid))

    def connectSignals(self):
        self.closeButton.clicked.connect(self.reject)
        self.openInFolderButton.clicked.connect(self.openInFolder)
        self.openFileButton.clicked.connect(self.openFile)
        self.reloadButton.clicked.connect(self.reloadFile)

    def openInFolder(self):
        fp = self.file_path
        if fp:
            subprocess.Popen('explorer /select,{}'.format(fp))
        self.reject()

    def openFile(self):
        fp = self.file_path
        if fp:
            QDesktopServices.openUrl(QUrl(QUrl.fromLocalFile(fp)))
        self.reject()

    def reloadFile(self):
        ChatApi.instance().downloadFile(self.file_uid, basename(self.file_path))
        self.reject()