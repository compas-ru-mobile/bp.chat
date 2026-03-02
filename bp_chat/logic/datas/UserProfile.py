
from bp_chat.core.tryable import ConsoleThread
from ..chat_api.api_object import ApiObject
from bp_chat.core.local_db_profiles import LocalDbProfiles

from datetime import datetime

class UserProfile(ApiObject):

    avatar_radius = 50
    photo_id = ""
    _name = ""
    third_name = ""
    surname = ""
    phone = ""
    email = ""
    position = ""
    user_day = None

    user = None

    def __init__(self, user, name):
        self.user = user
        self._name = name
        self._last_up_dt = None

    def __str__(self):
        return "Profile({}, {}, {}, photo:{})".format(
            self.getUserID(), self.getUserLogin(), self.getFullName(), self.getPhotoId())

    def load(self, initial=True):
        now = datetime.now()
        if initial or (self._last_up_dt == None or (now - self._last_up_dt).total_seconds() > 60 * 5):
            self._last_up_dt = now
            up = LocalDbProfiles.get_profile(
                        self.chatApi.server_uid, self.user.id)
            self.photo_id = up.photo or self.photo_id
            self._name = up.name
            self.third_name = up.third_name
            self.surname = up.surname
            self.phone = up.phone
            self.email = up.email
            self.position = up.position
            return self._name != None and self._name
        else:
            return None

    def setName(self, name):
        self._name = name

    def setSurname(self, name):
        self.surname = name

    def setPhone(self, name):
        self.phone = name

    def setEmail(self, name):
        self.email = name

    def setPosition(self, position):
        self.position = position

    def getUserID(self):
        return self.user.id

    def getUserLogin(self):
        return self.user.login

    def getUserType(self):
        return self.user.user_type

    def setUserType(self, user_type):
        if self.user:
            return self.user.setUserType(user_type)

    def getFullName(self):
        if len(self.third_name) == 0:
            if len(self.surname) == 0:
                ret = self._name
            else:
                ret = self.surname + " " + self._name
        else:
            if len(self.surname) == 0:
                ret = self._name + " " + self.third_name
            else:
                ret = self.surname + " " + self._name + " " + self.third_name
        return ret

    def getFullNameWithId(self):
        fullname = self.getFullName()
        login = self.getUserLogin()
        if login != None and len(login) > 0 and fullname != login:
            fullname += " (" + login + ")"
        return fullname

    def setPhotoId(self, _photo_id):
        self.photo_id = _photo_id

    def getPhotoId(self):
        return self.photo_id

    def getBitmap(self):
        btm = None
        if len(self.photo_id) > 0:
            return self.chat_api.getPhotoData(self.photo_id)
        return btm