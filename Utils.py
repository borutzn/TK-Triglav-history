import re
import os

import jinja2

template_dir = os.path.join(os.path.dirname(__file__), 'template')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


from flask import Flask
app = Flask(__name__)

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler('/tmp/TK.log', maxBytes=1*1024*1024, backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('TK start')


def log_info( s ):
    app.logger.info( s )


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



PICTURE_EXT = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file( filename ):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in PICTURE_EXT
