
from PyQt5.QtWidgets import QDialog, QAbstractItemView, QMessageBox
from PyQt5.QtCore import Qt #, WindowFlags
from PyQt5.QtGui import QColor, QPainter

from .ui.UiChatEditDialog import Ui_ChatEditDialog

from .delegates.UsersDictDelegate import UsersDictDelegate, UsersDictModel

from ..logic.datas.GroupChat import GroupChat
from ..logic.chat_api.ChatApi import ChatApi

from .views.UsersListView import UsersListView
from bp_chat.gui.common.langs import tr_w, tr


class ChatEditDialog(QDialog, Ui_ChatEditDialog):

    chat = None
    group_users = []

    def __init__(self, main_widget=None, chat=None, flags=Qt.Window, *args, **kwargs):
        self.mw = main_widget
        self.chat = chat
        super().__init__(main_widget)

        self.setupUi(self)
        self.retranslateUi(self)

        self.prepareView()
        self.initListView()
        self.connectSignals()

    def prepareView(self):
        flags = self.windowFlags()
        flags = int(flags)
        flags &= ~Qt.WindowContextHelpButtonHint
        flags = Qt.WindowFlags(flags)
        self.setWindowFlags(flags)

        if self.chat:
            self.showAllCheckBox.show()
            self.showAllCheckBox.setChecked(False)

            label_text = tr('Edit group')
            self.setWindowTitle(label_text)

            if ChatApi.instance().is_admin:
                label_text += ' #{}'.format(self.chat.chat_id)

            self.label.setText(label_text)
            self.inputChat.setText(self.chat.getName())

        else:
            self.showAllCheckBox.hide()
            self.showAllCheckBox.setChecked(True)

    def initListView(self):
        self.listView.hide()

        tr_w(self.label)
        self.setWindowTitle(tr(self.windowTitle()))

        tr_w(self.inputChat, placeHolder=True)
        tr_w(self.inputUser, placeHolder=True)
        tr_w(self.showAllCheckBox)
        tr_w(self.pushButtonOk)
        tr_w(self.pushButtonCancel)

        newListView = UsersListView(self)
        newListView.setFont(self.listView.font())
        newListView.setFrameShape(self.listView.frameShape())
        newListView.setVerticalScrollMode(self.listView.verticalScrollMode())
        newListView.setHorizontalScrollMode(self.listView.horizontalScrollMode())
        newListView.setSelectionMode(QAbstractItemView.MultiSelection)
        self.verticalLayout.replaceWidget(self.listView, newListView)
        self.listView = newListView
        self.updateListView(start=True)

    def updateListView(self, clear=False, start=False, filter_text=""):
        only_checked = not self.showAllCheckBox.isChecked()
        if start:
            delegate = UsersDictDelegate(self.listView, filter_text=filter_text, only_checked=only_checked)
            self.listView.setItemDelegate(delegate)
            self.listView.setModel(UsersDictModel(delegate))
        else:
            self.listView.model().updateMe(clear=clear, filter_text=filter_text, only_checked=only_checked)

    def connectSignals(self):
        self.inputUser.textChanged.connect(self.inputUserTextChanged)
        self.pushButtonOk.clicked.connect(self.accept)
        self.pushButtonCancel.clicked.connect(self._reject)
        self.showAllCheckBox.clicked.connect(self.updateListView)

    def inputUserTextChanged(self, text):
        self.updateListView(filter_text=text)

    def setCheckedUsers(self, checked_users):
        checked_users = tuple(map(str, checked_users))
        self.group_users = checked_users
        self.listView.setChecked(checked_users)
        self.updateListView()

    def showMessageBox(self, text):
        msg = QMessageBox()
        msg.setText(text)
        msg.setWindowFlags(
            Qt.Window |
            Qt.Popup
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def validateLineEditText(self, text):
        text = text.strip()
        if len(text) == 0:
            self.showMessageBox(tr('Group name field is empty'))
            return False
        return text

    def validateMembersCount(self, checked_users):
        if len(checked_users) < 1:
            self.showMessageBox(tr('Group members are not selected'))
            return False
        return checked_users

    def accept(self):
        group_name = self.validateLineEditText(self.inputChat.text())

        checked_users = self.getChecked()

        chatApi = ChatApi.instance()
        if str(chatApi.getCurrentUserId()) not in checked_users:
            checked_users.append(str(chatApi.getCurrentUserId()))

        checked_users = self.validateMembersCount(checked_users)

        if group_name and checked_users:
            super(ChatEditDialog, self).accept()

            chat_id = self.chat.chat_id if self.chat else -1

            # users = ""
            new_and_deleted = self.getNewAndDeleteUsers(checked_users)
            new_users = new_and_deleted.get("new_users")
            delete_users = new_and_deleted.get("delete_users")

            new_chat = chat_id == -1

            if new_chat:
                chatApi.createGroupChat(group_name, checked_users)
            else:
                int_chat_id = int(chat_id)
                if group_name != self.chat.getName():
                    chatApi.send(url="/group/change/", attrs={
                        "chat_id": int_chat_id,
                        "chat_name": group_name
                    })

                if len(new_users) > 0:
                    for user in new_users:
                        chatApi.send(url="/group/user/", attrs={
                            "chat_id": int_chat_id,
                            "user": int(user)
                        })

                if len(delete_users) > 0:
                    for user in delete_users:
                        chatApi.send(url="/group/user/", attrs={
                            "method": "POST",
                            "chat_id": int_chat_id,
                            "user": int(user)
                        })
            self.deleteLater()

    def getChecked(self):
        return list(self.listView.checked_users)

    def getNewAndDeleteUsers(self, checked_users):
        new_users = []
        result = {}
        gu = list(self.group_users)

        for user_id in checked_users:
            if user_id in gu:
                gu.remove(user_id)
            else:
                new_users.append(user_id)

        result['new_users'] = new_users
        result['delete_users'] = gu

        return result

    # FIXME hack auto dismiss, update: no hack
    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_Escape:
            self._reject()
        elif key_event.key() == Qt.Key_Return:
            self.accept()

    def _reject(self):
        self.reject()
        self.deleteLater()