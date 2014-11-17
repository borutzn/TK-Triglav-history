import sqlite3

from flask.ext.login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash


DbName = "TennisHistory.db"

'''
DROP TABLE Users;
CREATE TABLE Users( ident INTEGER PRIMARY KEY, username TEXT, utype INTEGER, pw_hash TEXT, email TEXT);
DELETE FROM Users;
'''
class User( UserMixin ):

    '''
        utype - user type: 0-reader, 1-(+comment), 2-author (+append), 3-editor (+edit), 4-admin (+delete)
    '''
    reader = 0
    comenter = 1
    author = 2
    editor = 3
    admin = 4
    
    def __init__( self, username, utype=0, password=None, pw_hash=None, email=None, ident=None):
        self.ident = ident
        self.username = username
        self.utype=utype
        if pw_hash:
            self.pw_hash = pw_hash
        elif password:
            self.pw_hash = generate_password_hash( password )
        else:
            self.pw_hash = None
        self.email = email

    def check_password( self, password ):
        return check_password_hash( self.pw_hash, password )


    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return True

    def get_id(self):
        return unicode(self.ident)

    def get_utype(self):
        return True #self.utype)

    @classmethod
    def get_byId(cls, ident):
        conn = sqlite3.connect(DbName)
        with conn:
            conn.row_factory = sqlite3.Row
            curs = conn.cursor()
            curs.execute( "SELECT * FROM Users WHERE ident=:ident", { "ident":ident } )
            user = curs.fetchone()
            conn.commit()
            return user

    
    @classmethod
    def get_byUser(cls, username):
        conn = sqlite3.connect(DbName)
        with conn:
            conn.row_factory = sqlite3.Row
            curs = conn.cursor()
            curs.execute( "SELECT * FROM Users WHERE username=:username",
                          { "username":username } )
            user = curs.fetchone()
            conn.commit()
            return user


    def put(self):
        conn = sqlite3.connect(DbName)
        curs = conn.cursor()

        curs.execute( "SELECT * FROM Users" )
        if curs.rowcount == 0:
            self.utype = self.admin
        conn.commit()                

        curs.execute( """INSERT INTO Users (username, pw_hash, email, utype)
                        VALUES (:username, :pw_hash, :email, :utype)""",
                        {"username":self.username, "pw_hash":self.pw_hash, "email":self.email, "utype":self.utype} )
        self.id = curs.lastrowid
        conn.commit()                



class Anonymous( AnonymousUserMixin ):

    def __init__(self):
        self.username = 'Guest'
        self.utype = 0
        self.email = ''
