import re
import os

import jinja2


files_dir = os.path.join(os.path.dirname(__file__), 'static/files')
template_dir = os.path.join(os.path.dirname(__file__), 'template')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


from flask import Flask
app = Flask(__name__)

PICTURE_EXT = {'png', 'jpg', 'jpeg', 'gif'}


if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler('/tmp/TK.log', maxBytes=1*1024*1024, backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('TK start')


def log_info(s):
    app.logger.info(s)


def valid_username(username):
    username_re = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return username_re.match(username)


def valid_password(password):
    password_re = re.compile(r"^.{3,20}$")
    return password_re.match(password)


def valid_email(email):
    email_re = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
    return email_re.match(email)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in PICTURE_EXT
