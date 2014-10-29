# -*- coding: utf-8 -*-

"""
Show Tenis history data of TK Triglav Kranj

data collected by Davor Žnidar
program by Borut Žnidar
"""

Production = False


import os
import logging
import re
import hmac
import datetime

import jinja2

from flask import render_template, request, redirect, flash, url_for
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required


from TennisData import TennisEvent

from Utils import valid_username, valid_password, valid_email
from Utils import Handler
from Utils import app

from User import User

from Upload import UploadCSV


			
@app.route("/player", methods=['GET'])
def Player():
    if request.method == 'GET':
        try:
                player = request.args.get('n')
        except ValueError:
                player = None

        if player == None:
                players = list(TennisEvent.players)
                players.sort(key=lambda player: player[0])
                return render_template("players.html", user="Borut", players=players )
        else:
        	events = TennisEvent.getPlayersEvents( player )
                return render_template("player.html", user="Borut", events=events )



@app.route("/comment", methods=['GET', 'POST'])
def EditComment():
    if request.method == 'GET':
        try:
                id = int(request.args.get('id'))
        except ValueError:
            return redirect(url_for("TennisMain"))

	event = TennisEvent.get( id )
	return render_template("comment.html", event=event, date=TennisEvent.date2user(event['date']) )

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            logging.error("POST")
            comment = request.form["comment"]
            if request.form["addcomment"] != "":
                comment += "; " + request.form["addcomment"]
            e = TennisEvent( comment=comment )
            logging.error("before update")
            e.updateComment( request.form["Id"] )
        return redirect(url_for("TennisMain"))


@app.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'GET':
	return render_template("add.html", event=[] )

    elif request.method == 'POST':
        logging.error( "ADD: "+str(request.form) )
        if request.form["Status"] == "Shrani":
            e = TennisEvent( date=request.form["date"], event=request.form["event"],
                         place=request.form["place"], category=request.form["category"],
                         result=request.form["result"], player=request.form["player"],
                         att1=request.form["att1"], att2=request.form["att2"],
                         att3=request.form["att3"], att4=request.form["att4"], 
                         comment=request.form["comment"])
            logging.error( "PUT: " )
            e.put()
        return redirect(url_for("TennisMain"))


@app.route("/edit", methods=['GET', 'POST'], defaults={'update':False} )
@app.route("/duplicate", methods=['GET', 'POST'], defaults={'update':True})
@login_required
def Edit( update ):
    if request.method == 'GET':
        try:
                id = int(request.args.get('id'))
        except ValueError:
            return redirect(url_for("TennisMain"))

	event = TennisEvent.get( id )
	return render_template("edit.html", event=event, date=TennisEvent.date2user(event['date']) )

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            e = TennisEvent( date=request.form["date"], event=request.form["event"],
                         place=request.form["place"], category=request.form["category"],
                         result=request.form["result"], player=request.form["player"],
                         att1=request.form["att1"], att2=request.form["att2"],
                         att3=request.form["att3"], att4=request.form["att4"], 
                         comment=request.form["comment"], source=request.form["vir"])
            logging.error( "Update: "+str(update) )
            if update:
                e.update( request.form["Id"] )
            else:
                e.put()
        return redirect(url_for("TennisMain"))

@app.route("/delete", methods=['GET', 'POST'])
@login_required
def Delete():
    if request.method == 'GET':
        try:
                id = int(request.args.get('id'))
        except ValueError:
            return redirect(url_for("TennisMain"))

	event = TennisEvent.get( id )
	return render_template("delete.html", event=event, date=TennisEvent.date2user(event['date']) )

    elif request.method == 'POST':
        if request.form["Status"][:5] == unicode("Izbriši"[:5]):
            TennisEvent.delete( request.form["Id"] )
        return redirect(url_for("TennisMain"))



PAGELEN = 15

@app.route("/")
def TennisMain():
        try:
		p = request.args.get('p')
                pos = int(p) if p else 0
	except ValueError:
		pos = 0

	events = TennisEvent.getEventsPage(pos, PAGELEN)
	eventsLen = TennisEvent.count()
	return render_template("main.html", events=events, production=Production,
                                players=TennisEvent.players[:20],
                                prevPage=pos-PAGELEN if pos>PAGELEN else 0,
                                nextPage=pos+PAGELEN if pos<eventsLen-PAGELEN else eventsLen-PAGELEN,
                                start=pos, count=eventsLen )

        

login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = os.urandom(24)
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = '$2a$16$PnnIgfMwk0jGX4SkHqS0P0'


@login_manager.user_loader
def load_user( userid ):
    u = User.get_byId( userid )
    if not u:
        return None
    return User( username=u['username'], pw_hash=u['pw_hash'], email=u['email'], ident=u['id'] )


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html", user_info="username")
    
    elif request.method == 'POST':
	username = request.form['username']
	password = request.form['password']
	rememberme = ("1" in request.form.getlist('remember'))
        u = User.get_byUser(username)
        if u:
            user = User( username=u['Username'], pw_hash=u['Pw_hash'], email=u['Email'], ident=u['Id'] )
            if user and user.is_authenticated() and user.check_password(password):
                login_user(user,remember=rememberme)
                return redirect(request.args.get("next") or url_for("TennisMain"))
        
        return render_template("login.html", username=username,
                               loginMsg="Invalid login.", password="")


@app.route("/signup", methods=['GET', 'POST'])
def Signup():
    if request.method == 'GET':
        return render_template("signup.html", entries=[])

    elif request.method == 'POST':
    	username = request.form['username']
	pass1 = request.form['password']
	pass2 = request.form['verify']
	email = request.form['email']
	userMsg = "That's not a valid username." if not valid_username(username) else ""
	pass1Msg = "That wasn't a valid password." if not valid_password(pass1) else ""
	pass2Msg = "Your password didn't match." if pass1 <> pass2 else ""
	emailMsg = "That's not a valid email." if not valid_email(email) else ""
	if (userMsg=="") and (pass1Msg=="") and (pass2Msg=="") and (emailMsg==""):
            user = User.get_byUser(username)
            if user != None:
                userMsg = "That user already exists."
	if (userMsg=="") and (pass1Msg=="") and (pass2Msg=="") and (emailMsg==""):
            user = User( username=username, password=pass1, email=email)
            user.put()
            login_user(user)
            return redirect(url_for("TennisMain"))

        return render_template("signup.html", username=username, userMsg=userMsg, password=pass1, 
            pass1Msg=pass1Msg, verify=pass2, pass2Msg=pass2Msg, email=email, emailMsg=emailMsg)


@app.route("/logout")
@login_required
def Logout():
	logout_user()
	return redirect(url_for("TennisMain"))




if __name__ == "__main__":
    if Production:
        app.run(host='0.0.0.0', port=80, debug=False)
    else:        
        app.run(host='127.0.0.1', port=80, debug=True)
