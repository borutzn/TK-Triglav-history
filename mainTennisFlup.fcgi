#!/usr/bin/python

# -*- coding: UTF-8 -*-

from cgi import escape
import sys, os
import logging
from flup.server.fcgi import WSGIServer

from mainTennis import app


logging.error( "START" )
if __name__ == "__main__":
	logging.error( "WSGIServer" )
	#WSGIServer(app,bindAddress='/tmp/tk.sock').run()
	WSGIServer(app).run()
