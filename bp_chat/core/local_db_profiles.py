from bp_chat.core.local_db_core import LocalDbCore
from bp_chat.core.tryable import tryable, ConsoleThread


class UserProfilePoint:

    def __init__(self, user_id, name, surname, third_name, email, photo, phone, position):
        self.user_id = user_id
        self.name = name
        self.surname = surname
        self.third_name = third_name
        self.email = email
        self.photo = photo
        self.phone = phone
        self.position = position


class LocalDbProfiles(LocalDbCore):

    '''
    id = Column(Integer(), primary_key=True, nullable=False, autoincrement=True)
    user_id = Column(Integer(), ForeignKey('users.id'), unique=True)
    user = relationship(Users)
    name = Column(String(100), nullable=False, default='')
    surname = Column(String(50), nullable=False, default='')
    third_name = Column(String(50), nullable=False, default='')
    email = Column(String(150), nullable=False, default='')
    photo = Column(String(150), nullable=False, default='')
    phone = Column(String(20), nullable=True, default='')
    position = Column(String(20), nullable=True, default='')
    '''

    @classmethod
    def startup(cls, conn):
        #print('[ LocalDbProfiles ]->[ startup ]')
        _ = conn.execute('''CREATE TABLE IF NOT EXISTS user_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server VARCHAR(50) NOT NULL,
            user_id INTEGER NOT NULL,
            name VARCHAR(100),
            surname VARCHAR(50),
            third_name VARCHAR(50),
            email VARCHAR(150),
            photo VARCHAR(150),
            phone VARCHAR(20),
            position VARCHAR(20)
        )''')
        conn.commit()

    @classmethod
    @LocalDbCore.into_db_executor
    def get_profiles(cls, server):
        conn = cls.get_instance().conn
        cursor = conn.cursor()
        d = {}
        cursor.execute('SELECT user_id, name, surname, third_name, email, photo, phone, position FROM user_info WHERE server=?', (server,))
        for row in cursor:
            d[row[0]] = UserProfilePoint(**row)
        return d

    @classmethod
    @tryable
    def get_profile(cls, server, user_id):

        point = cls.get_synced('user_info', server, 'user_id', user_id,
            names=('name', 'surname', 'third_name', 'email', 'photo', 'phone', 'position'),
            defaults=('', '', '', '', '', '', ''))

        return point

    @classmethod
    @tryable
    def add_profile(cls, server, user_id, name, surname, third_name, email, photo, phone, position):

        return cls.add_synced('user_info', server, 'user_id', user_id,
            names=('name', 'surname', 'third_name', 'email', 'photo', 'phone', 'position'),
            values=(name, surname, third_name, email, photo, phone, position))


LocalDbCore.register(LocalDbProfiles)
