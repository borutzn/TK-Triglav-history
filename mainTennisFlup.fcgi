#!/usr/bin/python

# -*- coding: UTF-8 -*-

import logging
from flup.server.fcgi import WSGIServer

from mainTennis import app


if __name__ == "__main__":
    logging.error("WSGIServer start")
    WSGIServer(app).run()
