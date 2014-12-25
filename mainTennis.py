#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Show Tenis history data of TK Triglav Kranj

data collected by Davor Žnidar
program by Borut Žnidar on 12.12.2014
"""

appname = "TK-Triglav-history"
Production = True

import string
import csv
import re
import os
import logging
import difflib

from flask import render_template, request, redirect, url_for
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug import secure_filename


from TennisData import TennisEvent, TennisPlayer

from Utils import app, log_info, valid_username, valid_password, valid_email, allowed_file, files_dir

from User import User, Anonymous



@app.route("/player", methods=['GET', 'POST'])
def Player():
    if request.method == 'GET' :
        try:
            playerName = request.args.get('n')
        except ValueError:
            playerName = None
        if playerName is not None:
            player = TennisPlayer.get( playerName )
            events = TennisEvent.getPlayersEvents( playerName )
            #app.logger.info( "Player: " + str(player) )
            return render_template("player.html", events=events, playername=playerName, player=player )

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
        #log_info( 'editPlayer: ' + unicode(ident) )
        if ident <> None:
            player = TennisPlayer.get( ident )
            #log_info( "GOT " + unicode(player) )
            if player == None:
                player = TennisPlayer( Name=ident )
                #log_info( "GOT " + unicode(player.Name) )
            return render_template("editPlayer.html", player=player, ident=ident )

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            name = request.form['Name']
            born = request.form['Born']
            died = request.form['Died']
            comment = request.form['Comment']
            picture = request.form['Picture']
            file = request.files['upload']
            if file and allowed_file(file.filename):
                picture = os.path.join( "players", secure_filename(file.filename) )
                filename = os.path.join( files_dir, picture )
                file.save( os.path.join( filename ) )
            p = TennisPlayer( Name=name, Born=born, Died=died, Comment=comment, Picture=picture )
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
        app.logger.error( "Com: "+ str(event) )
        return render_template("editComment.html", event=event, date=TennisEvent.date2user(event['Date']) )

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


@app.route("/edit", methods=['GET', 'POST'], defaults={'update':True} )
@app.route("/duplicate", methods=['GET', 'POST'], defaults={'update':False}, endpoint='Duplicate' )
@login_required
def EditEvent( update ):
    if request.method == 'GET':
        try:
            ident = int(request.args.get('id'))
        except ValueError:
            return redirect(url_for("TennisMain"))

        event = TennisEvent.get( ident )
        #log_info( "RENDER " + str(event['LocalDate']) )
        return render_template("editEvent.html", event=event )

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            log_info( "CreateEvent" + str(request.form) )
            e = TennisEvent( date=request.form["date"], event=request.form["event"],
                         place=request.form["place"], category=request.form["category"],
                         result=request.form["result"], player=request.form["player"],
                         att1=request.form["att1"], att2=request.form["att2"],
                         att3=request.form["att3"], att4=request.form["att4"], 
                         comment=request.form["comment"], source=request.form["source"])
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
        log_info( "DELETE: " + str(event) )
        return render_template("delete.html", event=event, date=TennisEvent.date2user(event['Date']) )
        # CORRECT date=...
        
    elif request.method == 'POST':
        if request.form["Status"][:5] == unicode("Izbriši"[:5]):
            TennisEvent.delete( request.form["Id"] )
        return redirect(url_for("TennisMain"))


@app.route("/reload", methods=['GET'])
@login_required
def Reload():
    if request.method == 'GET':
        TennisEvent.clearData()
    return redirect( request.args.get("next") )



@app.route("/correct", methods=['GET', 'POST'])
@login_required
def Correct():
    if request.method == 'GET':
        try:
            ident = int(request.args.get('id'))
            att = int(request.args.get('att'))
            fdir = request.args.get('d')
            fname = request.args.get('f')
            next = request.args.get('next')
        except ValueError:
            return redirect(url_for("TennisMain"))

        fnames = []
        try:
            log_info( os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/files/'+fdir) )
            for f in os.listdir( os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/files/'+fdir) ):
                s = list(f)
                #for i, c in enumerate(s):
                #    if ord(c) >= 128:
                #        s[i] = "_"
                f = "".join(s)
                fnames.append( { 'fname':f, 'fit':("%d%%" % (100.0*difflib.SequenceMatcher(None,fname,f).ratio())) } )
        except ValueError:
            # No files in directory - nothing to select from
            return redirect(url_for("TennisMain"))
            
        fnames = sorted(fnames, key=lambda data: int(data['fit'][:-1]), reverse=True)
        if len(fnames) > 10:
            fnames= fnames[:10]
        return render_template("correct.html", fdir=fdir, fname=fname, fnames=fnames, ident=ident, att=att, next=next )

    elif request.method == 'POST':
        if request.form["Status"][:5] == unicode("Shrani"[:5]):
            TennisEvent.updateAtt( request.form["ident"],request.form["att"], request.form["fname"] )
        return redirect( request.form["next"] )



PAGELEN = 15

@app.route("/")
def TennisMain():
    #  http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
    log_info( "request for /" )
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

        

'''
   0. Leto - datum
   1. * - datum je datum vira
   2. Dogodek
   3. Kraj
   4. Spol - M, Z
   5. Dvojice - D
   6. Kategorija
   7. Uvrstitev
   8. Igralci
   9. Priloga 1
  10. Priloga 2
  11. Priloga 3
'''
att_ext = [".pdf",".PDF",".jpg",".JPG",".jpeg",".JPEG",".png",".PNG"]
def convertEntry( row ):
    entry = {}
    lastCol = 13
    while (row[lastCol] == "") and lastCol > 1:
        lastCol -= 1
    if lastCol >= 2:
        r = re.search("^(\d{1,2})\.(\d{1,2})\.(\d{2,4})", row[0])
        if r:
            (d,m,y) = (int(r.group(1)), int(r.group(2)), int(r.group(3)))
            entry["date"] = unicode("%02d.%02d.%04d" % (d,m,y))
        else:
            (d,m,y) = (0, 0, int(row[0]))
            entry["date"] = unicode("%02d.%02d.%04s" % (d,m,y))
        entry["event"] = unicode(row[2], "utf-8")
        entry["place"] = unicode(row[3], "utf-8")
        entry["sex"] = unicode(row[4], "utf-8")
        entry["doubles"] = unicode(row[5], "utf-8")
        entry["category"] = unicode(row[6], "utf-8")
        entry["result"] = unicode(row[7], "utf-8")
        entry["player"] = unicode(string.strip(row[8]), "utf-8")
        r = re.search("\((\d{1,2})\)$", entry["player"])
        if r:
            age = r.group(1) # save in the database
            entry["player"] = entry["player"][:-5]
        entry["eventAge"] = unicode(row[6], "utf-8")
        entry["comment"] = unicode("")
        if row[1] == '*':
            entry["comment"] = u"vnešen datum vira; "
        entry["att1"] = unicode(string.strip(row[9]), "utf-8")
        if entry["att1"] != "" and not any(x in entry["att1"] for x in att_ext):
            entry["comment"] += entry["att1"] + "; "
            entry["att1"] = ""
        if entry["att1"] != "":
            if d==0 and m==0:
                entry["att1"] = ("%d" % (y)) + '_' + entry["att1"]
            else:
                entry["att1"] = ("%d.%d.%d" % (y,m,d)) + '_' + entry["att1"]

        entry["att2"] = unicode(string.strip(row[10]), "utf-8")
        if entry["att2"] != "" and not any(x in entry["att2"] for x in att_ext):
            entry["comment"] += entry["att2"] + "; "
            entry["att2"] = ""
        if entry["att2"] != "":
            if d==0 and m==0:
                entry["att2"] = ("%d" % (y)) + '_' + entry["att2"]
            else:
                entry["att2"] = ("%d.%d.%d" % (y,m,d)) + '_' + entry["att2"]

        entry["att3"] = unicode(string.strip(row[11]), "utf-8")
        if entry["att3"] != "" and not any(x in entry["att3"] for x in att_ext):
            entry["comment"] += entry["att3"] + "; "
            entry["att3"] = ""
        if entry["att3"] != "":
            if d==0 and m==0:
                entry["att3"] = ("%d" % (y)) + '_' + entry["att3"]
            else:
                entry["att3"] = ("%d.%d.%d" % (y,m,d)) + '_' + entry["att3"]

        entry["att4"] = unicode(string.strip(row[12]), "utf-8")
        if entry["att4"] != "" and not any(x in entry["att4"] for x in att_ext):
            entry["comment"] += entry["att4"] + "; "
            entry["att4"] = ""
        if entry["att4"] != "":
            if d==0 and m==0:
                entry["att4"] = ("%d" % (y)) + '_' + entry["att4"]
            else:
                entry["att4"] = ("%d.%d.%d" % (y,m,d)) + '_' + entry["att4"]

        return True, entry
    else:
        return False, None


'''
  - generate data from Execel: Export to text (Unicode)
  - convert to UTF-8
  - change/reduce all pictures with: mogrify -resize 500 */*JPG; jpg
'''
@app.route('/Upload', methods=['GET', 'POST'])
def UploadCSV():
    if request.method == 'GET':
        return render_template("uploadFile.html")
    elif request.method == 'POST':
        line = 0
        f_upload = request.files['file']
        local_fname = os.path.join( files_dir, secure_filename(f_upload.filename) )
        f_upload.save( local_fname )
        with open(local_fname, 'rb') as csvfile:
            stringReader = csv.reader(csvfile,delimiter="\t",quotechar='"')
            for row in stringReader:
                line += 1
                if line == 1:
                    continue
                #log_info("Row: %s" % (row) )
                (ok, entry) = convertEntry( row )
                #log_info("Entry: %s - %s" % (str(ok), entry))
                if ok:
                    if line % 20 == 0:
                        log_info( "IMPORT l.%d: %s - %s" % (line, entry['date'], entry['event']))
                    e = TennisEvent( date=entry["date"], event=entry["event"],
                                     place=entry["place"], category=entry["category"],
                                     result=entry["result"], player=entry["player"],
                                     comment=entry["comment"], att1=entry["att1"],
                                     att2=entry["att2"], att3=entry["att3"], att4=entry["att4"])
                    e.put()
        return redirect(url_for("TennisMain"))




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
                app.logger.info( "AUDIT - User login: " + user.username )
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
            app.logger.info( "AUDIT - New user: " + user )
            return redirect(url_for("TennisMain"))

        return render_template("signup.html", username=username, userMsg=userMsg, password=pass1, 
            pass1Msg=pass1Msg, verify=pass2, pass2Msg=pass2Msg, email=email, emailMsg=emailMsg)


@app.route("/logout")
@login_required
def Logout():
    app.logger.info( "AUDIT - User logout: " + str(current_user.username) )
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



@app.route("/shutdown", methods=['GET', 'POST'])
@login_required
def Shutdown():
    if request.method == 'GET':
        return render_template("shutdown.html" )
            
    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            os.system( "shutdown -h 0" )
        return redirect(request.args.get("next") or url_for("TennisMain"))




if __name__ == "__main__":
    if Production:
        log_info( appname + " start standalone production" )
        app.run(host='0.0.0.0', port=8080, debug=False)
    else:        
        log_info( appname + " start standalone development" )
        app.run(host='127.0.0.1', port=80, debug=True)
else:
    log_info( appname + " start" )
