import sqlite3

from flask.ext.login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from Utils import log_info


DbName = "TennisHistory.db"

'''
DROP TABLE Users;
CREATE TABLE Users( ident INTEGER PRIMARY KEY, username TEXT, utype INTEGER, active BOOLEAN, pw_hash TEXT, email TEXT);
DELETE FROM Users;
'''


class User(UserMixin):
    '''
        utype - user type: 0-reader, 1-(+comment), 2-author (+append), 3-editor (+edit), 4-admin (+delete)
    '''
    reader = 0
    commenter = 1
    author = 2
    editor = 3
    data admin = 4
    app admin = 5

    def __init__(self, username, utype=reader, active=True, password=None, pw_hash=None, email=None, ident=None):
        self.ident = ident
        self.username = username
        self.utype = utype
        self.active = active
        if pw_hash:
            self.pw_hash = pw_hash
        elif password:
            self.pw_hash = generate_password_hash(password)
        else:
            self.pw_hash = None
        self.email = email

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return True

    def get_id(self):
        return unicode(self.ident)

    def get_utype(self):
        return True  # self.utype)

    @classmethod
    def get_by_id(cls, ident):
        conn = sqlite3.connect(DbName)
        with conn:
            conn.row_factory = sqlite3.Row
            curs = conn.cursor()
            curs.execute("SELECT * FROM Users WHERE ident=:ident", {"ident": ident})
            user = curs.fetchone()
            conn.commit()
            return user

    @classmethod
    def get_by_user(cls, username):
        conn = sqlite3.connect(DbName)
        with conn:
            conn.row_factory = sqlite3.Row
            curs = conn.cursor()
            curs.execute("SELECT * FROM Users WHERE username=:username",
                         {"username": username})
            user = curs.fetchone()
            conn.commit()
            return user

    @classmethod
    def get_users(cls):
        conn = sqlite3.connect(DbName)
        with conn:
            conn.row_factory = sqlite3.Row
            curs = conn.cursor()
            curs.execute("SELECT * FROM Users ORDER BY ident")
            users = curs.fetchall()
            conn.commit()
            return users

    def put(self):
        conn = sqlite3.connect(DbName)
        curs = conn.cursor()

        curs.execute("SELECT * FROM Users")
        if curs.rowcount == 0:
            self.utype = self.admin
        conn.commit()                

        curs.execute("""INSERT INTO Users (username, pw_hash, utype, active, email)
                     VALUES (:username, :pw_hash, :utype, :active, :email)""",
                     {"username": self.username, "pw_hash": self.pw_hash, "utype": self.utype, "active": self.active,
                      "email": self.email})
        self.id = curs.lastrowid
        conn.commit()                

    def update(self, iden):
        conn = sqlite3.connect(DbName)
        curs = conn.cursor()

        log_info("before update")
        curs.execute("""UPDATE Users SET utype=:utype, active=:active, email=:email WHERE ident=:ident""",
                     {'utype': self.utype, 'active': self.active, 'email': self.email, 'ident': iden})
        log_info("before commit")
        conn.commit()                
        log_info("after comit")


class Anonymous(AnonymousUserMixin):

    def __init__(self):
        self.username = 'Guest'
        self.utype = User.reader
        self.active = True
        self.email = ''
