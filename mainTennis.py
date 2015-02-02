#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Show Tenis history data of TK Triglav Kranj

data collected by Davor Žnidar
program by Borut Žnidar on 2.1.2015

check syntactic errors with: "python mainTennis.py runserver -d"
"""

appname = "TK-Triglav-History"

from config import Production, PAGELEN

import os
import string
import logging
import difflib

from flask import render_template, request, redirect, url_for, session, flash, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename


from TennisData import TennisEvent, TennisPlayer

from Utils import app, log_info, valid_username, valid_password, valid_email, allowed_file, files_dir

from User import User, Anonymous


@app.route("/player", methods=['GET', 'POST'])
def show_player():
    if request.method == 'GET':
        try:
            player_name = request.args.get('n')
        except ValueError:
            player_name = None
        if player_name is not None:
            player = TennisPlayer.get(player_name)
            events = TennisEvent.get_players_events(player_name)
            # app.logger.info( "Player: " + str(player) )
            return render_template("player.html", events=events, playername=player_name, player=player)

    search = ""
    if request.method == 'POST':
        search = request.form['search']

    # log_info( "search: " + str(search) )
    # log_info( "players: " + str(TennisEvent.players) )
    if search == "":
        players = list(TennisEvent.players)
    else:
        players = list()
        for p in TennisEvent.players:
            if search in p[0]:
                # app.logger.info( "found: (%s) in %s" %  (search, p[0]) )
                players.append(p)
        # app.logger.info( "players: " + str(players) )

    return render_template("players.html", players=players, search=search)


@app.route("/editPlayer", methods=['GET', 'POST'])
@login_required
def edit_player():
    if request.method == 'GET':
        try:
            iden = request.args.get('id')
        except ValueError:
            iden = None
        # log_info( 'editPlayer: ' + unicode(iden) )
        if iden is not None:
            player = TennisPlayer.get(iden)
            # log_info( "GOT " + unicode(player) )
            if player is None:
                player = TennisPlayer(name=iden)
                # log_info( "GOT " + unicode(player.Name) )
            return render_template("editPlayer.html", player=player, ident=iden)

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            name = request.form['Name']
            born = request.form['Born']
            died = request.form['Died']
            comment = request.form['Comment']
            picture = request.form['Picture']
            upload_file = request.files['upload']
            if upload_file and allowed_file(upload_file.filename):
                picture = os.path.join("players", secure_filename(upload_file.filename))
                filename = os.path.join(files_dir, picture)
                upload_file.save(os.path.join(filename))
            p = TennisPlayer(name=name, born=born, died=died, comment=comment, picture=picture)
            p.update()

    return redirect(request.args.get("next") or url_for("show_player"))


@app.route("/comment", methods=['GET', 'POST'])
def edit_comment():
    if request.method == 'GET':
        try:
            ident = int(request.args.get('id'))
        except ValueError:
            flash(u"Napaka: comment - napačen identifikator.")
            return redirect(request.args.get("next") or url_for("tennis_main"))

        event = TennisEvent.get(ident)
        log_info("Com: " + str(event))
        return render_template("editComment.html", event=event, date=TennisEvent.date2user(event['Date']))

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            comment = request.form["comment"]
            if request.form["addcomment"] != "":
                comment += "; " + request.form["addcomment"]
            ev = TennisEvent(comment=comment)
            ev.update_comment(request.form["Id"])
        return redirect(request.args.get("next") or url_for("tennis_main"))


@app.route("/add", methods=['GET', 'POST'])
def add_event():
    if request.method == 'GET':
        return render_template("addEvent.html", event=[])

    elif request.method == 'POST':
        logging.error("ADD: "+str(request.form))
        if request.form["Status"] == "Shrani":
            ev = TennisEvent(date=request.form["date"], event=request.form["event"],
                             place=request.form["place"], category=request.form["category"],
                             result=request.form["result"], player=request.form["player"],
                             att1=request.form["att1"], att2=request.form["att2"],
                             att3=request.form["att3"], att4=request.form["att4"],
                             comment=request.form["comment"])
            ev.put()
        return redirect(request.args.get("next") or url_for("tennis_main"))


@app.route("/edit", methods=['GET', 'POST'], defaults={'update': True})
@app.route("/duplicate", methods=['GET', 'POST'], endpoint='duplicate', defaults={'update': False})
@login_required
def edit_event(update):
    if request.method == 'GET':
        try:
            ident = int(request.args.get('id'))
        except ValueError:
            flash(u"Napaka: edit_event - napačen identifikator.")
            return redirect(request.args.get("next") or url_for("tennis_main"))

        event = TennisEvent.get(ident)
        atts_dir = os.path.join(files_dir, event["Date"][:4])
        log_info("ATTS: %s" % atts_dir)
        atts = [""] + [f for f in os.listdir(atts_dir)]
        return render_template("editEvent.html", event=event, atts=atts)

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            # log_info("ATT1: %s - %s, %s." % (request.form["att1"]==request.form["select_att1"],
            #                                  request.form["att1"], request.form["select_att1"]))
            ev = TennisEvent(date=request.form["date"], event=request.form["event"],
                             place=request.form["place"], category=request.form["category"],
                             result=request.form["result"], player=request.form["player"],
                             att1=request.form["att1"], att2=request.form["att2"],
                             att3=request.form["att3"], att4=request.form["att4"],
                             comment=request.form["comment"], source=request.form["source"])
            log_info("UPDATE: " + str(update))
            if update:
                ev.update(request.form["Id"])
            else:
                ev.put()
        return redirect(request.args.get("next") or url_for("tennis_main"))


@app.route("/delete", methods=['GET', 'POST'])
@login_required
def delete():
    if request.method == 'GET':
        try:
            ident = int(request.args.get('id'))
        except ValueError:
            flash(u"Napaka: delete - napačen identifikator.")
            return redirect(request.args.get("next") or url_for("tennis_main"))

        event = TennisEvent.get(ident)
        log_info("DELETE: " + str(event))
        return render_template("delete.html", event=event, date=TennisEvent.date2user(event['Date']))

    elif request.method == 'POST':
        if request.form["Status"][:5] == unicode("Izbriši"[:5]):
            TennisEvent.delete(request.form["Id"])
        return redirect(request.args.get("next") or url_for("tennis_main"))


@app.route("/reload", methods=['GET'])
@login_required
def data_reload():
    if request.method == 'GET':
        TennisEvent.clear_data()
    return redirect(request.args.get("next") or url_for("tennis_main"))


@app.route("/correct", methods=['GET', 'POST'])
@login_required
def correct():
    if request.method == 'GET':
        try:
            ident = int(request.args.get('id'))
            att = int(request.args.get('att'))
            fdir = request.args.get('d')
            fname = request.args.get('f')
            next_pg = request.args.get('next')
        except (ValueError, TypeError) as e:
            log_info("ERROR: %s" % str(e))
            flash(u"Napaka: correct - napačen parameter.")
            return redirect(request.args.get("next") or url_for("tennis_main"))

        fnames = []
        try:
            log_info(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/files/'+fdir))
            for f in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/files/'+fdir)):
                s = list(f)
                f = "".join(s)
                fnames.append({'fname': f, 'fit': ("%d%%" % (100.0*difflib.SequenceMatcher(None, fname, f).ratio()))})
        except ValueError:
            # No files in directory - nothing to select from
            flash(u"Napaka: ni razpoložljivih datotek.")
            return redirect(request.args.get("next") or url_for("tennis_main"))

        fnames = sorted(fnames, key=lambda data: int(data['fit'][:-1]), reverse=True)
        if len(fnames) > 10:
            fnames = fnames[:10]
        return render_template("correct.html", fdir=fdir, fname=fname, fnames=fnames,
                               ident=ident, att=att, next=next_pg)

    elif request.method == 'POST':
        if request.form["Status"][:5] == unicode("Shrani"[:5]):
            TennisEvent.update_att(request.form["ident"], request.form["att"], request.form["fname"])
        return redirect(request.args.get("next") or url_for("tennis_main"))


@app.route("/", methods=['GET', 'POST'])
def tennis_main():
    #  http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
    event_filter = ""
    if request.method == 'GET':
        try:
            p = request.args.get('p')
            pos = int(p) if p else 0
        except ValueError:
            pos = 0
    elif request.method == 'POST':
        select_player = request.form['select_player']
        event_filter = request.form['event_filter']
        select_year = request.form['select_year']
        if select_player != "":
            return redirect(url_for("show_player") + "?n=" + select_player)
        elif event_filter != "":
            pos = 0
        else:
            pos = TennisEvent.get_year_pos(select_year)
    else:
        pos = 0

    events = TennisEvent.get_events_page(pos, page_len=PAGELEN, event_filter=event_filter, collapsed_groups=())
    all_events_len = TennisEvent.count()
    log_info("GET_EVENTS: %d" % (len(events)))
    # log_info( "GET_EVENTS: %d %s" % (len(events), str(events)))
    if len(events) == 0:
        flash(u"Noben dogodek ne ustreza.")
        return redirect(request.args.get("next") or url_for("tennis_main"))

    return render_template("main.html", events=events, production=Production,
                           players=TennisEvent.players, years=TennisEvent.Years, top_players=TennisEvent.top_players,
                           prevPage=pos-PAGELEN if pos > PAGELEN else 0,
                           nextPage=pos+PAGELEN if pos < all_events_len-PAGELEN else all_events_len-PAGELEN,
                           start=pos, count=all_events_len)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = Anonymous
app.secret_key = os.urandom(24)
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = '$2a$16$PnnIgfMwk0jGX4SkHqS0P0'


@login_manager.user_loader
def load_user(userid):
    u = User.get_by_id(userid)
    if not u:
        return None
    return User(username=u['username'], pw_hash=u['pw_hash'], utype=u['utype'], active=u['active'], email=u['email'],
                ident=u['ident'])


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html", user_info="username")
    
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = ("1" in request.form.getlist('remember'))
        u = User.get_by_user(username)
        if u:
            user = User(username=u['Username'], pw_hash=u['Pw_hash'], email=u['Email'], ident=u['Ident'])
            if user and user.is_authenticated() and user.check_password(password):
                login_user(user, remember=remember_me)
                session['user'] = user.username
                log_info("AUDIT: User %s login." % user.username)
                flash(u"Prijava uspešna.")
                return redirect(request.args.get("next") or url_for("tennis_main"))
        
        session.pop('user', None)
        flash(u"Prijava neuspešna.")
        return render_template("login.html", username=username, password="")


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template("signup.html", entries=[])

    elif request.method == 'POST':
        username = request.form['username']
        pass1 = request.form['password']
        pass2 = request.form['verify']
        email = request.form['email']
        failed = False
        if not valid_username(username):
            failed = True
            flash(u"Neustrezno uporabniško ime.")
        if not valid_password(pass1):
            failed = True
            flash(u"Neustrezno geslo.")
        if pass1 != pass2:
            failed = True
            flash(u"Geslo se ne ujema.")
        if not valid_email(email):
            failed = True
            flash(u"Neustrezen poštni predal.")
        if not failed:
            user = User.get_by_user(username)
            if user is not None:
                failed = True
                flash(u"Uporabnik že obstaja.")
        if failed:
            return render_template("signup.html", username=username, password=pass1, verify=pass2, email=email)

        user = User(username=username, password=pass1, email=email)
        user.put()
        login_user(user)
        session['user'] = None
        log_info("AUDIT: New user %s created." % user.username)
        flash(u"Kreiran in prijavljen nov uporabnik.")
        return redirect(request.args.get("next") or url_for("tennis_main"))


@app.route("/logout")
@login_required
def logout():
    log_info("AUDIT: User %s logout." % str(current_user.username))
    logout_user()
    session.pop('user', None)
    flash(u"Odjava uspešna.")
    return redirect(request.args.get("next") or url_for("tennis_main"))


@app.route("/editUser", methods=['GET', 'POST'])
@login_required
def edit_user():
    if request.method == 'GET':
        if 'id' in request.args:
            try:
                iden = int(request.args.get('id'))
            except ValueError:
                flash(u"Napaka: edit_user - napačen identifikator.")
                return redirect(request.args.get("next") or url_for("tennis_main"))

            user = User.get_by_id(iden)
            return render_template("editUser.html", user=user)
        else:
            users = User.get_users()
            return render_template("listUsers.html", users=users)
            
    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            u = User(username=request.form["username"], utype=request.form["utype"],
                     active=request.form["active"], email=request.form["email"])
            u.update(request.form["ident"])
        return redirect(request.args.get("next") or url_for("edit_user"))


@app.route("/upload_picture", methods=['GET', 'POST'])
@login_required
def upload_picture():
    if request.method == 'GET':
        return render_template("uploadPicture.html", years=TennisEvent.Years)
    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            year = request.form["select_year"]
            upload_file = request.files['upload']
            if upload_file and allowed_file(upload_file.filename):
                picture_dir = os.path.join(files_dir, secure_filename(year))
                if not os.path.exists(picture_dir):
                    log_info("Audit: directory %s created." % picture_dir)
                    os.makedirs(picture_dir)
                picture = os.path.join(picture_dir, secure_filename(upload_file.filename))
                upload_file.save(picture)
                log_info("Audit: picture %s uploaded." % picture)
                flash(u"Slika uspešno prenešena.")
            else:
                flash(u"NAPAKA: Neustrezna slika.")
        return redirect(request.args.get("next") or url_for("tennis_main"))


@app.route("/events.csv", methods=['GET'], endpoint="events.csv", defaults={'action': 'events', 'fmt': 'csv'})
@app.route("/people.csv", methods=['GET'], endpoint="people.csv", defaults={'action': 'people', 'fmt': 'csv'})
@app.route("/events.json", methods=['GET'], endpoint="events.json", defaults={'action': 'events', 'fmt': 'json'})
@app.route("/people.json", methods=['GET'], endpoint="people.json", defaults={'action': 'people', 'fmt': 'json'})
@login_required
def export(action, fmt):
    if request.method == 'GET':
        log_info("AUDIT: Data export (%s,%s) by %s." % (action, fmt, str(current_user.username)))
        if action == 'events':
            if fmt == "json":
                return TennisEvent.export('J')
            elif fmt == "csv":
                return TennisEvent.export('C')
        elif action == 'people':
            if fmt == "json":
                return TennisPlayer.jsonify()


@app.route("/audit", methods=['GET'])
@login_required
def audit():
    out = ""
    with open('/tmp/TK.log', 'r') as f:
        for l in f:
            if l[30:37] != "AUDIT: ":
                continue
            p = string.find(l, ' [', 37)
            out += "%s %s\r\n" % (l[:16], l[37:p])
    f.close()
    return Response(out, mimetype='text/plain')


@app.route("/shutdown", methods=['GET', 'POST'])
@login_required
def shutdown():
    if request.method == 'GET':
        log_info("AUDIT: System shutdown requested by %s." % str(current_user.username))
        return render_template("shutdown.html")
            
    elif request.method == 'POST':
        if request.form["Status"] == "Ugasni":
            log_info("AUDIT: System shutdown confirmed and executed")
            os.system("sudo shutdown -h 0")
        flash(u"Če je bilo ugašanje uspešno, stran ne bo več dosegljiva. :-)")
        return redirect(request.args.get("next") or url_for("tennis_main"))


if __name__ == "__main__":
    if Production:
        log_info(appname + ": start standalone production")
        app.run(host='127.0.0.1', port=8080, debug=False)
    else:        
        log_info(appname + ": start standalone development")
        app.run(host='127.0.0.1', port=80, debug=True)
else:
    log_info(appname + ": start")
