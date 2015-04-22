# -*- coding: utf-8 -*-

from config import LOG_FILE, LOG_SIZE, LOG_COUNT, ATT_EXT

import re
import os
import csv
import json
import codecs
import cStringIO
import urllib

import jinja2


base_dir = os.path.dirname(__file__)
files_dir = os.path.join(base_dir, 'static', 'files')
template_dir = os.path.join(base_dir, 'template')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


from flask import Flask, request, session
from flask_login import current_user
app = Flask(__name__)
app.secret_key = os.urandom(30)


if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler

    # http://stackoverflow.com/questions/1407474/does-python-logging-handlers-rotatingfilehandler-allow-creation-of-a-group-writa
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=LOG_SIZE, backupCount=LOG_COUNT)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    # file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'))
    os.chmod(LOG_FILE, 0664)
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('TK start')


# possible fields: datetime.datetime.today().ctime(), request.data, request.remote_addr, request.method, request.path
#                  ', '.join([': '.join(x) for x in request.headers])
#  http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
@app.before_request
def pre_request_settings():
    session.modified = True  # alternative: session.permanent = True
    if 'text/html' in request.headers['Accept']:
        # https://www.kirsle.net/wizards/flask-session.py
        # app.logger.info("COOKIE: %s" % str(request.cookies))  # https://www.kirsle.net/wizards/flask-session.py
        app.logger.info("AUDIT: %s/%s/%s (%s: %s) requested %s" % (str(current_user.username),
                        session.get("user", "/"), session.get("_id", "")[-5:],
                        ip_to_country(request.remote_addr), request.remote_addr, request.endpoint))


# @app.after_request
# def post_request_settings(response):
#    s = session.get("user",None)
#    if s:
#        app.logger.info("SESSION_post: %s, %s, %s" % (s, session.get("_id", "")[-5:], response.mimetype))
#    return response


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
           filename.rsplit('.', 1)[1] in ATT_EXT


ip_cache = {}


def ip_to_country(ip):
    if ip not in ip_cache:
        response = urllib.urlopen("http://freegeoip.net/json/%s" % ip).read()
        result = json.loads(response.decode('utf8')).get('country_name', '/')
        ip_cache[ip] = result if result != "" else "/"
    return ip_cache[ip]


class UnicodeCsvWriter:
    # A CSV writer which will write rows to CSV file "f", which is encoded in the given encoding.

    def __init__(self, dialect=csv.excel, encoding="utf-8", **kwds):
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.encoder = codecs.getincrementalencoder(encoding)()

    def convert_row(self, row):
        # log_info("CONVERT ROW: "+unicode(row))
        self.writer.writerow([s.encode("utf-8") if s else '' for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        return data
