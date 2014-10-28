import string
import random
import re
import hashlib
import hmac

import jinja2

from Utils import valid_username, valid_password, valid_email

#global jinja_env


def make_salt(length = 5):
	return ''.join(random.choice(string.letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256(name + pw + salt).hexdigest()
	return '%s|%s' % (salt, h)

def valid_pw(name, password, h):
	salt = h.split('|')[0]
	return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
	return db.Key.from_path('users', group)				


login_user = ""

class Users():
        '''
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty()
        '''
        
	@classmethod
	def by_id(cls, uid):
		#if Users.get_by_id( int(uid), parent=users_key() ):
			#logging.info( "by_id: %d: %s." % (int(uid), Users.get_by_id(int(uid), parent=users_key()).username) )
		#else:
			#logging.info( "by_id: %s: None." % uid  )
		return Users.get_by_id(int(uid), parent=users_key())

	@classmethod
	def by_name(cls, name):
		u = Users.all().filter('username =', name).get()
		return u

	@classmethod
	def register(cls, name, pw, email = None):
		pw_hash = make_pw_hash(name, pw)
		return Users(parent = users_key(),
					username = name,
					password = pw_hash,
					email = email)

	@classmethod
	def login(cls, name, pw):
		u = cls.by_name(name)
		if u and valid_pw(name, pw, u.password):
			#logging.info( "Users.login return:" + u.username )
			return u
		#else:
			#logging.info( "Users.login return: None" )
			
	@classmethod
	def get_username(cls,handler):
		user_id = handler.read_secure_cookie('user_id')
		if user_id:
			username = Users.by_id(user_id).username
			if not valid_username(username):
				username = ""
		else:
			username = ""
		return username


