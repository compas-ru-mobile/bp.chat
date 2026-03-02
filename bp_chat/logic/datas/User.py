
from .UserProfile import UserProfile


SYMS_0 = 'QWERTYUIOPASDFGHJKLZXCVBNM'
SYMS_0 += SYMS_0.lower()
SYMS_1 = 'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ'
SYMS_1 += SYMS_1.lower()
SYMS = '1234567890-_=+!$#^&*()[]/:/"|?%@~`' + SYMS_0 + SYMS_1


class User:

    STATUS_OFFLINE = 0
    STATUS_ONLINE = 1
    STATUS_SLEEP = 2

    USER_TYPE_MANAGER = "2"
    USER_TYPE_SIMPLE = "1"
    USER_TYPE_GUEST = "0"

    #user_id = None
    _name = None
    chat = None
    status = STATUS_OFFLINE
    is_bot = False

    def __init__(self, name, id, user_type, is_bot=False):
        self._name = self.fix_name(name)
        self.id = id
        self.user_type = str(user_type) # FIXME ...
        self.profile = UserProfile(self, name)
        self.is_bot = is_bot
        self.devices = {}

    @property
    def login(self):
        return self.fix_name(self._name)

    @property
    def name(self):
        return self.fix_name(self._name) #return self.profile.getFullName()

    def fix_name(self, name):
        return ''.join( a for a in name if a in SYMS )

    def setUserType(self, user_type):
        self.user_type = str(user_type)

    def is_online(self):
        return self.status != User.STATUS_OFFLINE

    def is_sleep(self):
        return self.status == User.STATUS_SLEEP

    def is_guest(self):
        return self.user_type == User.USER_TYPE_GUEST

    def is_manager(self):
        return self.user_type == User.USER_TYPE_MANAGER

    def getStatusName(self):
        if self.status == self.STATUS_ONLINE:
            return "ONLINE"
        elif self.status == self.STATUS_SLEEP:
            return "SLEEP"
        return "OFFLINE"

    def __str__(self):
        return 'User({}, {})'.format(self.id, self.name)

    def __repr__(self):
        return self.__str__()