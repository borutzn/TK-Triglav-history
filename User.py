import datetime
import logging

import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash


DbName = "TennisHistory.db"

'''
DROP TABLE Users;
CREATE TABLE Users( Id-->Ident INTEGER PRIMARY KEY, Username TEXT, Pw_hash TEXT, Email TEXT);
DELETE FROM Users;
'''
class User(object):

    def __init__( self, username, utyp=None, password=None, pw_hash=None, email=None, ident=None, born=None, description=None):
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
        self.born = born
        self.description = description

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


    @classmethod
    def get_byId(cls, ident):
        conn = sqlite3.connect(DbName)
        with conn:
            conn.row_factory = sqlite3.Row
            curs = conn.cursor()
            curs.execute( "SELECT * FROM Users WHERE id=:ident", { "ident":ident } )
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

        curs.execute( """INSERT INTO Users (username,pw_hash,email)
                        VALUES (:username, :pw_hash, :email)""",
                        {"username":self.username, "pw_hash":self.pw_hash, "email":self.email} )
        self.id = curs.lastrowid
        conn.commit()                
