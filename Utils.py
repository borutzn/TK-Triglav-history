import random
import re
import os

import jinja2

template_dir = os.path.join(os.path.dirname(__file__), 'template')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


from flask import Flask
app = Flask(__name__)



def valid_username(username):
	UsernameRE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
	#logging.info( "valid_username:" + str(username) )
	return UsernameRE.match(username)
	
def valid_password(password):
	PasswordRE = re.compile(r"^.{3,20}$")
	return PasswordRE.match(password)
	
def valid_email(email):
	EmailRE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
	return EmailRE.match(email)

	
	
class Handler():
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
		
	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)
		
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def set_secure_cookie(self, name, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))
		#logging.info( "set cookie %s --> %s=%s" % (val, name, cookie_val) )

	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)

	def login(self, user):
		self.set_secure_cookie('user_id', str(user.key().id()))

	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		uid = self.read_secure_cookie('user_id')
		self.user = uid and Users.by_id(uid)
