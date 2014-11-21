#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Show Tenis history data of TK Triglav Kranj

data collected by Davor Žnidar
program by Borut Žnidar on 7.11.2014
"""

Production = True

import os
import logging
import difflib

from flask import render_template, request, redirect, url_for
from flask.ext.login import LoginManager, login_user, logout_user, login_required


from TennisData import TennisEvent, TennisPlayer

from Utils import app, log_info, valid_username, valid_password, valid_email

from User import User, Anonymous



@app.route("/player", methods=['GET', 'POST'])
def Player():
    if request.method == 'GET' :
        try:
            player = request.args.get('n')
        except ValueError:
            player = None
        if player <> None:
            events = TennisEvent.getPlayersEvents( player )
            return render_template("player.html", events=events, id=player )

    search = ""
    if request.method == 'POST':
        search = request.form['search']

    #app.logger.info( "search: " + str(search) )
    #app.logger.info( "players: " + str(TennisEvent.players) )
    if search == "":
        players = list(TennisEvent.players)
    else:
        players = list()
        for p in TennisEvent.players:
            if search in p[0]:
                #app.logger.info( "found: (%s) in %s" %  (search, p[0]) )
                players.append( p )
        #app.logger.info( "players: " + str(players) )

    players.sort(key=lambda player: player[0])
    return render_template("players.html", players=players, search=search )



@app.route("/editPlayer", methods=['GET', 'POST'])
@login_required
def EditPlayer():
    if request.method == 'GET' :
        try:
            ident = request.args.get('id')
        except ValueError:
            ident = None
        app.logger.info( 'editPlayer: ' + str(ident) )
        if ident <> None:
            player = TennisPlayer.get( ident )
            app.logger.info( "GOT " + str(player) )
            if player == None:
                player = TennisPlayer( name=ident )
            app.logger.info( "GOT " + str(player) )
            return render_template("editPlayer.html", player=player, ident=ident )

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            name = request.form['name']
            born = request.form['born']
            died = request.form['died']
            comment = request.form['comment']
            picture = request.form['picture']
            p = TennisPlayer( name=name, born=born, died=died, comment=comment, picture=picture )
            p.update()

    return redirect(url_for("Player"))


@app.route("/comment", methods=['GET', 'POST'])
def EditComment():
    if request.method == 'GET':
        try:
            ident = int(request.args.get('id'))
        except ValueError:
            return redirect(url_for("TennisMain"))

        event = TennisEvent.get( ident )
        return render_template("editComment.html", event=event, date=TennisEvent.date2user(event['date']) )

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            comment = request.form["comment"]
            if request.form["addcomment"] != "":
                comment += "; " + request.form["addcomment"]
            e = TennisEvent( comment=comment )
            e.updateComment( request.form["Id"] )
        return redirect(url_for("TennisMain"))


@app.route("/add", methods=['GET', 'POST'])
def AddEvent():
    if request.method == 'GET':
        return render_template("addEvent.html", event=[] )

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
@app.route("/duplicate", methods=['GET', 'POST'], defaults={'update':True}, endpoint='Duplicate' )
@login_required
def EditEvent( update ):
    if request.method == 'GET':
        try:
            ident = int(request.args.get('id'))
        except ValueError:
            return redirect(url_for("TennisMain"))

        event = TennisEvent.get( ident )
        return render_template("editEvent.html", event=event )

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            e = TennisEvent( date=request.form["date"], event=request.form["event"],
                         place=request.form["place"], category=request.form["category"],
                         result=request.form["result"], player=request.form["player"],
                         att1=request.form["att1"], att2=request.form["att2"],
                         att3=request.form["att3"], att4=request.form["att4"], 
                         comment=request.form["comment"], source=request.form["vir"])
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
            ident = int(request.args.get('id'))
        except ValueError:
            return redirect(url_for("TennisMain"))

        event = TennisEvent.get( ident )
        return render_template("delete.html", event=event, date=TennisEvent.date2user(event['date']) )
        # CORRECT date=...
        
    elif request.method == 'POST':
        if request.form["Status"][:5] == unicode("Izbriši"[:5]):
            TennisEvent.delete( request.form["Id"] )
        return redirect(url_for("TennisMain"))


@app.route("/correct", methods=['GET', 'POST'])
@login_required
def Correct():
    if request.method == 'GET':
        try:
            ident = int(request.args.get('id'))
            att = int(request.args.get('att'))
            fdir = request.args.get('d')
            fname = request.args.get('f')
        except ValueError:
            return redirect(url_for("TennisMain"))

        fnames = []
        try:
            for f in os.listdir(url_for('static',filename="files/"+fdir)):
                s = list(f)
                for i, c in enumerate(s):
                    if ord(c) >= 128:
                        s[i] = "_"
                f = "".join(s)
                fnames.append( { 'fname':f, 'fit':("%d%%" % (100.0*difflib.SequenceMatcher(None,fname,f).ratio())) } )
        except ValueError:
            # No files in directory - nothing to select from
            return redirect(url_for("TennisMain"))
            
        fnames = sorted(fnames, key=lambda data: int(data['fit'][:-1]), reverse=True)
        if len(fnames) > 15:
            fnames= fnames[:15]
            return render_template("correct.html", fdir=fdir, fname=fname, fnames=fnames, id=ident, att=att )

    elif request.method == 'POST':
        logging.error( "UPDATE ATT" )
        TennisEvent.updateAtt( request.form["id"],request.form["att"], request.form["fname"] )
        logging.error( "UPDATE ATT DONE" )
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
    for e in events: # Why this check?
        if e['Att1'] == None:
            logging.error( "err: "+e['Event']+", "+str(e['Att1']) )
    return render_template("main.html", events=events, production=Production,
                players=TennisEvent.players[:20],
                prevPage=pos-PAGELEN if pos>PAGELEN else 0,
                nextPage=pos+PAGELEN if pos<eventsLen-PAGELEN else eventsLen-PAGELEN,
                start=pos, count=eventsLen )

        

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = Anonymous
app.secret_key = os.urandom(24)
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = '$2a$16$PnnIgfMwk0jGX4SkHqS0P0'


@login_manager.user_loader
def load_user( userid ):
    u = User.get_byId( userid )
    if not u:
        return None
    return User( username=u['username'], pw_hash=u['pw_hash'], utype=u['utype'], active=u['active'], email=u['email'], ident=u['ident'] )


@app.route("/login", methods=['GET', 'POST'])
def Login():
    if request.method == 'GET':
        return render_template("login.html", user_info="username")
    
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        rememberme = ("1" in request.form.getlist('remember'))
        u = User.get_byUser(username)
        if u:
            user = User( username=u['Username'], pw_hash=u['Pw_hash'], email=u['Email'], ident=u['Ident'] )
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


@app.route("/editUser", methods=['GET', 'POST'])
@login_required
def EditUser():
    if request.method == 'GET':
        if 'id' in request.args:
            try:
                ident = int(request.args.get('id'))
            except ValueError:
                return redirect(url_for("TennisMain"))

            user = User.get_byId( ident )
            return render_template("editUser.html", user=user )
        else:
            users = User.get_Users()
            return render_template("listUsers.html", users=users )
            
    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            u = User( username=request.form["username"], utype=request.form["utype"], 
                      active=request.form["active"], email=request.form["email"])
            ident = request.form["ident"]
            u.update( request.form["ident"] )
        return redirect(url_for("EditUser"))



if __name__ == "__main__":
    if Production:
        log_info( "start production version" )
        app.run(host='0.0.0.0', port=80, debug=False)
    else:        
        log_info( "start development version" )
        app.run(host='127.0.0.1', port=80, debug=True)
