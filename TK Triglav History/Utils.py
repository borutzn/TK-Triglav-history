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
