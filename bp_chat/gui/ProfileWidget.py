from PyQt5.QtWidgets import QWidget, QItemDelegate, QToolButton, QFileDialog, QInputDialog, QLineEdit
from PyQt5.QtCore import Qt, QSize, QPointF
from PyQt5.QtGui import QColor, QIcon, QPainter

from .ui.UiProfileWidget import Ui_ProfileWidget
from .core.draw import icon_from_file, pixmap_from_file, change_widget_background_color, pixmap_from_icon, pixmap_from_icon_rounded

from ..logic.chat_api.ChatApi import ChatApi
from .common.system_info import get_download_path
from .common.langs import tr, tr_w


class ProfileWidget(QWidget, Ui_ProfileWidget):

    main_widget = None
    userProfile = None
    openingUserId = None

    def __init__(self, parent, main_widget, flags=Qt.Window, *args, **kwargs):
        super().__init__(parent)

        self.main_widget = main_widget

        self.setupUi(self)
        self.retranslateUi(self)

        self.initView()
        self.connectSignals()

        self.initAdmin()

    def initAdmin(self):
        if ChatApi.instance().is_admin:
            self.changeButtonsWidget.setVisible(True)
            self.setEditVisible(self.editFormWidget.isVisible())
            self.makeAdminButton.show()
        else:
            self.changeButtonsWidget.setVisible(False)
            self.setEditVisible(False)
            self.makeAdminButton.hide()

    def editProfileButtonClicked(self, yes=True):
        if ChatApi.instance().is_admin:
            self.setEditVisible(not self.editFormWidget.isVisible())
        else:
            self.setEditVisible(False)

    def editAvatarButtonClicked(self):
        filename, ok = QFileDialog.getOpenFileName(self, tr("Choose photo"), get_download_path(), "Images (*.jpg *.png)")
        if filename:
            ChatApi.instance().sendFile(filepath=filename, user_avatar=self.userProfile.getUserID())


    def editLoginButtonClicked(self):
        login, ok = QInputDialog.getText(self, tr("Change login"),
                                   tr("Please input new login here:"), QLineEdit.Normal, self.userProfile.getUserLogin())
        login = login.strip()
        if ok and len(login) > 0 and login != self.userProfile.getUserLogin():
            ChatApi.instance().send(url='/users/rename/',attrs={
                'method': 'POST',
                'user_id': self.userProfile.getUserID(),
                'new_user_name': login
            })
            self.getProfileUpdate()

    def editUserTypeButtonClicked(self):
        types = ['guest', 'simple', 'manager']
        user_type = self.userProfile.getUserType()
        if user_type == None:
            return
        user_type, ok = QInputDialog.getItem(self, tr("Change user type"), tr("Select one of types list"), types, int(user_type), False)
        if ok:
            user_type = types.index(user_type)
            if user_type != self.userProfile.getUserType():
                ChatApi.instance().send(url='/users/rename/',attrs={'method':'POST', 'user_id': self.userProfile.getUserID(), 'new_user_type': user_type})
                self.userProfile.setUserType(user_type)

    def getProfileUpdate(self):
        ChatApi.instance().send(url='/user/profile/', attrs={
            'user_id': self.userProfile.getUserID()
        })

    def setEditVisible(self, value):
        self.editFormWidget.setVisible(value)
        self.textBrowser.setVisible(not value)

    def initView(self):
        change_widget_background_color(self, QColor(255, 255, 255))
        change_widget_background_color(self.toolBarWidget, QColor(255, 193, 7))

        tr_w(self.label)

        self.userAvatarLabel.setPixmap(pixmap_from_file("favicon", 50, 50))
        self.profileCloseButton.setIcon(icon_from_file("cancel"))

    def connectSignals(self):
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.editProfileButton.clicked.connect(self.editProfileButtonClicked)
        self.editAvatarButton.clicked.connect(self.editAvatarButtonClicked)
        self.editLoginButton.clicked.connect(self.editLoginButtonClicked)
        self.editUserTypeButton.clicked.connect(self.editUserTypeButtonClicked)
        self.profileCloseButton.clicked.connect(self.closeButtonClicked)
        self.makeAdminButton.clicked.connect(self.makeAdminClicked)
        self.activateButton.clicked.connect(self.activateClicked)

    def setOpeningUserId(self, value):
        self.openingUserId = value

    def onBackClick(self):
        self.main_widget.showChatsList(withTitle=True)

    def updateProfile(self, userProfile):
        self.to_avatar = None

        self.userProfile = userProfile

        fullname = userProfile.getFullNameWithId()

        add = ''
        if userProfile.user_day:
            add += '<div>{} - {} {}</div>'.format(userProfile.user_day[0], userProfile.user_day[1],
                                                  '({})'.format(userProfile.user_day[3]) if len(userProfile.user_day) > 3 else '')

        fin_add = ''
        devices = userProfile.user.devices
        if devices:
            fin_add = '<br>'.join(['{} ({})'.format(ver, platform) for ver, platform in devices])

        html = '''<html><body>
<h3>{name}</h3>
<div>{position}</div>{add}
<br>
<div><b>{phones_title}</b>: {phones}</div>
<div><b>{mails_title}</b>: {mails}</div>
<div>{fin_add}</div>
</body></html>'''.format(
            name=fullname,
            phones_title=tr("Phones"),
            phones=self.list_line_to_html(str(userProfile.phone)),
            mails_title=tr("Mails"),
            mails=self.list_line_to_html(str(userProfile.email)),
            position=str(userProfile.position),
            add=add, fin_add=fin_add
        )

        self.textBrowser.setHtml(html)

        bitmap = userProfile.getBitmap()

        if bitmap == None:
            self.userAvatarLabel.setPixmap(pixmap_from_file("favicon", 100, 100))
        else:
            #self.userAvatarLabel.setPixmap(pixmap_from_icon(bitmap, 100, 100))
            pixmap = pixmap_from_icon_rounded(bitmap, to_size=(100, 100), border_radius=10)
            if pixmap:
                self.userAvatarLabel.setPixmap(pixmap)

        self._updateEditProfile(userProfile)

        self.initAdmin()

    def _updateEditProfile(self, userProfile):
        self.nameLineEdit.setText(userProfile._name)
        self.surnameLineEdit.setText(userProfile.surname)
        self.phoneLineEdit.setText(str(userProfile.phone))
        self.emailLineEdit.setText(str(userProfile.email))
        self.positionLineEdit.setText(str(userProfile.position))

    def saveButtonClicked(self):
        self.userProfile.setName(self.nameLineEdit.text())
        self.userProfile.setSurname(self.surnameLineEdit.text())
        self.userProfile.setEmail(self.emailLineEdit.text())
        self.userProfile.setPhone(self.phoneLineEdit.text())
        self.userProfile.setPosition(self.positionLineEdit.text())
        ChatApi.instance().send(url='/user/profile/', attrs={
            'method': 'POST',
            'user_id': self.userProfile.getUserID(),
            'name': self.userProfile._name,
            'surname': self.userProfile.surname,
            'email': self.userProfile.email,
            'phone': self.userProfile.phone,
            'position': self.userProfile.position,
        })
        self.setEditVisible(False)

    def makeAdminClicked(self):
        ChatApi.instance().makeAdmin(self.userProfile.getUserID())

    def activateClicked(self):
        #user = ChatApi.instance().getUser(self.userProfile.getUserID())
        ChatApi.instance().activateUser(self.userProfile.getUserID(), False)

    def closeButtonClicked(self):
        self.main_widget.closeCurrentChat()

    def list_line_to_html(self, line):
        lst = line.split(";")
        if len(lst) == 0:
            return "-"
        return '<ul><li>' + '</li><li>'.join(lst) + "</li></ul>"