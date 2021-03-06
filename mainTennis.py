#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Show Tenis history data of TK Triglav Kranj

data collected by Davor Žnidar
program by Borut Žnidar on 18.2.2017

rPi config:

1. console as apps
    su - apps
    cd TKTriglavHistory
    git pull origin

2. console as pi
    tail -f /tmp/TK.log &
    sudo /etc/init.d/lighttpd restart


check syntactic errors with: "python mainTennis.py runserver -d"

    /var/log/lighttpd/
    /etc/lighttpd
"""

from config import Production, LOG_FILE

import os
import re
import sys
import glob
import math
import shutil
import string
import random
import difflib

from flask import render_template, request, redirect, url_for, session, flash, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename


from TennisData import TennisEvent, TennisPlayer, EventSource

from Utils import app, log_info, valid_email, valid_password, allowed_file, allowed_image, files_dir_os

from User import User, Anonymous

appname = "TK-Triglav-History"


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
            return render_template("player.html", events=events, playername=player_name, player=player)

    search = ""
    if request.method == 'POST':
        search = request.form['search']

    if search == "":
        players = list(TennisEvent.players)
    else:
        players = list()
        for p in TennisEvent.players:
            if search in p[0]:
                players.append(p)

    return render_template("players_list.html", players=players, search=search)


@app.route("/editPlayer", methods=['GET', 'POST'])
@login_required
def edit_player():
    if request.method == 'GET':
        try:
            iden = request.args.get('id')
        except ValueError:
            iden = None
        if iden is not None:
            player = TennisPlayer.get(iden)
            if player is None:
                player = TennisPlayer(name=iden)
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
                filename = os.path.join(files_dir_os, picture)
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
            log_info("Error: wrong edit_comment identifier (%s)" % request.args.get('id'))
            flash(u"Napaka: comment - napačen identifikator.")
            return redirect(request.args.get("next") or url_for("tennis_events_old"))

        event = TennisEvent.get(ident)
        return render_template("editComment.html", event=event, date=TennisEvent.date2user(event['Date']))

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            comment = request.form["comment"]
            if request.form["addcomment"] != "":
                comment += "; " + request.form["addcomment"]
            ev = TennisEvent(comment=comment)
            ev.update_comment(request.form["Id"])
        return redirect(request.args.get("next") or url_for("tennis_events_old"))


@app.route("/addEvent1", methods=['GET', 'POST'], endpoint='add_event1', defaults={"step": 1})
@app.route("/addEvent2", methods=['GET', 'POST'], endpoint='add_event2', defaults={"step": 2})
def add_event(step):
    if request.method == 'GET':
        date = request.args.get('d', "")
        if step == 1:
            return render_template("addEvent-S1.html", date=TennisEvent.date2user(date) if date != "" else "")
        elif step == 2:
            atts_dir = os.path.join(files_dir_os, secure_filename(date[:4]))
            try:
                atts = [""] + [f for f in os.listdir(atts_dir) if allowed_file(f)]
            except OSError:
                atts = []
            atts.sort()
            players = list(TennisEvent.players)
            return render_template("addEvent-S2.html", date=TennisEvent.date2user(date), players=players, atts=atts)

    elif request.method == 'POST' and step == 1:
        date = TennisEvent.date2db(request.form["date"])
        if request.form["Status"] == "Dodaj vir":
            return redirect(url_for("upload_picture", y=date[:4],
                                    next=url_for("add_event1", d=date)))
        elif request.form["Status"] == "Dodaj dogodek":
            return redirect(url_for("add_event2", d=date, next=url_for("add_event1", d=date)))

    elif request.method == 'POST' and step == 2:
        if request.form["Status"] == "Shrani":
            ev = TennisEvent(date=request.form["date"], event=request.form["event"],
                             place=request.form["place"], category=request.form["category1"],
                             result=request.form["result1"], player=request.form["player1"],
                             att1=request.form["att1"], att2=request.form["att2"],
                             att3=request.form["att3"], att4=request.form["att4"],
                             comment=request.form["comment"])
            ev.put(fetch=False)
            for p in range(2, 7):
                if request.form["player%d" % p] != "":
                    ev.category = request.form["category%d" % p]
                    ev.result = request.form["result%d" % p]
                    ev.player = request.form["player%d" % p]
                    ev.put(fetch=False)
            TennisEvent.fetch_data(force=True, sources=False)
            return redirect(url_for("tennis_events_old", y=ev.date[-4:]))
    return redirect(request.args.get("next") or url_for("tennis_events_old"))


@app.route("/edit", methods=['GET', 'POST'], defaults={'update': True})
@app.route("/duplicate", methods=['GET', 'POST'], endpoint='duplicate', defaults={'update': False})
@login_required
def edit_event(update):
    if request.method == 'GET':
        try:
            ident = int(request.args.get('id'))
        except ValueError:
            log_info("Error: wrong edit_event identifier (%s)" % request.args.get('id'))
            flash(u"Napaka: edit_event - napačen identifikator.")
            return redirect(request.args.get("next") or url_for("tennis_events_old"))

        event = TennisEvent.get(ident)
        atts_dir = os.path.join(files_dir_os, secure_filename(event["Date"][:4]))
        atts = [""] + [f for f in os.listdir(atts_dir) if allowed_file(f)]
        atts.sort()
        return render_template("editEvent.html", event=event, atts=atts)

    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            ev = TennisEvent(date=request.form["date"], event=request.form["event"],
                             place=request.form["place"], category=request.form["category"],
                             result=request.form["result"], player=request.form["player"],
                             att1=request.form["att1"], att2=request.form["att2"],
                             att3=request.form["att3"], att4=request.form["att4"],
                             comment=request.form["comment"], source=request.form["source"])
            if update:
                ev.update(request.form["Id"])
            else:
                ev.put()
        return redirect(request.args.get("next") or url_for("tennis_events_old"))


@app.route("/delete", methods=['GET', 'POST'])
@login_required
def delete():
    if request.method == 'GET':
        try:
            ident = int(request.args.get('id'))
        except ValueError:
            log_info("Error: wrong delete identifier (%s)" % request.args.get('id'))
            flash(u"Napaka: delete - napačen identifikator.")
            return redirect(request.args.get("next") or url_for("tennis_events_old"))

        event = TennisEvent.get(ident)
        log_info("Delete: " + str(event))
        return render_template("delete.html", event=event, date=TennisEvent.date2user(event['Date']))

    elif request.method == 'POST':
        if request.form["Status"][:5] == unicode("Izbriši"[:5]):
            TennisEvent.delete(request.form["Id"])
        return redirect(request.args.get("next") or url_for("tennis_events_old"))


@app.route("/reload", methods=['GET'])
@login_required
def data_reload():
    if request.method == 'GET':
        TennisEvent. fetch_data(force=True, players=True, sources=True)
    return redirect(request.args.get("next") or url_for("tennis_events_old"))


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
            log_info("Error: %s" % str(e))
            flash(u"Napaka: correct - napačen parameter.")
            return redirect(request.args.get("next") or url_for("tennis_events_old"))

        fnames = []
        try:
            for f in os.listdir(os.path.join(files_dir_os, secure_filename(fdir))):
                s = list(f)
                f = "".join(s)
                fnames.append({'fname': f, 'fit': ("%d%%" % (100.0*difflib.SequenceMatcher(None, fname, f).ratio()))})
        except ValueError:
            # No files in directory - nothing to select from
            flash(u"Napaka: ni razpoložljivih datotek.")
            return redirect(request.args.get("next") or url_for("tennis_events_old"))

        fnames = sorted(fnames, key=lambda data: int(data['fit'][:-1]), reverse=True)
        if len(fnames) > 10:
            fnames = fnames[:10]
        return render_template("correct.html", fdir=fdir, fname=fname, fnames=fnames,
                               ident=ident, att=att, next=next_pg)

    elif request.method == 'POST':
        if request.form["Status"][:5] == unicode("Shrani"[:5]):
            TennisEvent.update_att(request.form["ident"], request.form["att"], request.form["fname"])
        return redirect(request.args.get("next") or url_for("tennis_events_old"))


@app.route("/old", methods=['GET', 'POST'])
def tennis_events_old():
    event_filter = ""
    show_stat = "0"
    if request.method == 'GET':
        try:
            year = request.args.get('y')
            if year not in TennisEvent.Years:
                year = TennisEvent.Years[0]
            show_stat = request.args.get('s')
        except ValueError:
            year = TennisEvent.Years[0]
            log_info("Error: wrong main year (%s) -> setting %s" % (request.args.get('y'), year))
    elif request.method == 'POST':
        select_player = request.form['select_player']
        event_filter = request.form['event_filter']
        select_year = request.form['select_year']
        if select_player != "":
            return redirect(url_for("show_player") + "?n=" + select_player)
        elif event_filter != "":
            year = None
        else:
            return redirect(url_for("tennis_events_old") + "?y=" + select_year)
            # year = select_year
    else:
        year = request.args.get('y')

    events = TennisEvent.get_events_by_year(year=year, event_filter=event_filter)
    if len(events) == 0:
        flash(u"Noben dogodek ne ustreza.")
        log_info("Error: GET / - no event")
        return redirect(request.args.get("next") or url_for("tennis_events_old"))

    pictures = []
    for src in TennisEvent.sources:
        if src[0] == year and allowed_image(src[1]):
            pictures.append(src)

    year_len = len(TennisEvent.Years)
    year_idx = TennisEvent.Years.index(year if year else TennisEvent.Years[0])
    return render_template("main.html", events=events, production=Production,
                           players=TennisEvent.players, years=TennisEvent.Years, top_players=TennisEvent.top_players,
                           prevPage=TennisEvent.Years[max(year_idx-1, 0)],
                           nextPage=TennisEvent.Years[min(year_idx+1, year_len-1)],
                           count=TennisEvent.count(), showStat=show_stat)


@app.route("/first", methods=['GET'])
def tennis_start():
    pictures = TennisEvent.get_oneyear_pictures(year=TennisEvent.Years[0], max_years=6)
    return render_template("first.html", pictures=pictures)


@app.route("/", methods=['GET'])
def tennis_events():
    if request.method == 'GET':
        try:
            year_param = request.args.get('y')
            year = year_param or TennisEvent.Years[0]
        except ValueError:
            year_param, year = None, TennisEvent.Years[0]
            log_info("Error: wrong main year (%s) -> setting %s" % (request.args.get('y'), year))

        try:
            player_name = request.args.get('p') or ""
        except ValueError:
            player_name = None
            log_info("Error: wrong player (%s) -> setting %s" % (request.args.get('p'), player_name))

        try:
            event_filter = request.args.get('f') or ""
        except ValueError:
            event_filter = ""
            log_info("Error: wrong filter (%s) -> setting %s" % (request.args.get('f'), filter))
    else:
        return redirect(request.args.get("next") or url_for("tennis_events"))

    log_info("PARAMS: %s, %s, %s" % (year, player_name, event_filter))

    if year not in TennisEvent.Years:
        year_param, year = None, TennisEvent.Years[0]

    events = TennisEvent.get_oneyear_events(year=year,  player=player_name, event_filter=event_filter)
    if len(events) == 0:
        flash(u"Noben dogodek ne ustreza.")
        log_info("Error: GET / - no event")
        for y in TennisEvent.Years:
            events = TennisEvent.get_oneyear_events(year=y, player=player_name, event_filter=event_filter)
            if len(events) > 0:
                break
        # not good... return redirect(request.args.get("next") or url_for("tennis_events"))

    year = events[0][1]['Date'][:4]
    i = TennisEvent.Years.index(year)
    prev_y = TennisEvent.Years[i-1 if i > 0 else 0]
    next_y = TennisEvent.Years[i+1 if i < len(TennisEvent.Years)-1 else 0]
    if player_name:
        player = TennisPlayer.get(player_name)
        pictures = TennisEvent.get_oneplayer_pictures(player=player_name)
        return render_template("players.html", events=events, players=TennisEvent.players, pictures=pictures,
                               event_filter=event_filter, year=year, player_name=player_name,
                               player=player, prev_y=prev_y, next_y=next_y)
    else:
        pictures = TennisEvent.get_oneyear_pictures(year=year_param, max_years=6)
        return render_template("events.html", events=events, players=TennisEvent.players, pictures=pictures,
                               event_filter=event_filter, year=year, player_name=player_name,
                               prev_y=prev_y, next_y=next_y)


@app.route("/events_year", methods=['GET'], endpoint='events_year', defaults={'one_player': False})
@app.route("/players_year", methods=['GET'], endpoint='players_year', defaults={'one_player': True})
def tennis_events_year(one_player):
    if request.method != 'GET':
        return

    try:
        year = request.args.get('y')
        if year not in TennisEvent.Years:
            year = TennisEvent.Years[0]
    except ValueError:
        year = TennisEvent.Years[0]
        log_info("Error: wrong main year (%s) -> setting %s" % (request.args.get('y'), year))
    try:
        to_year = request.args.get('t')
        if year not in TennisEvent.Years:
            to_year = TennisEvent.Years[-1]
    except ValueError:
        to_year = TennisEvent.Years[-1]
        log_info("Error: wrong main year (%s) -> setting %s" % (request.args.get('y'), year))
    try:
        player_name = request.args.get('p')
    except ValueError:
        player_name = None
        log_info("Error: wrong player (%s) -> setting %s" % (request.args.get('p'), player_name))
    try:
        event_filter = request.args.get('f') or ""
    except ValueError:
        event_filter = ""
        log_info("Error: wrong filter (%s) -> setting %s" % (request.args.get('f'), filter))

    log_info("get year_events %s, %s, %s-%s, %s" % (one_player, player_name, year, to_year, event_filter))
    events = TennisEvent.get_oneyear_events(year=year, player=player_name, event_filter=event_filter)
    if len(events) == 0:
        next_y = "0"
    else:
        i = TennisEvent.Years.index(events[0][1]['Date'][:4])
        if i < len(TennisEvent.Years)-1:
            next_y = TennisEvent.Years[i+1]
            if to_year and next_y > to_year:
                next_y = "0"
        else:
            next_y = "0"
    return render_template("players_year.html" if one_player else "events_year.html",
                           events=events, next_y=next_y, to_y=to_year,
                           player_name=player_name, event_filter=event_filter)


@app.route("/pictures", methods=['GET'])
def tennis_pictures():
    try:  # 'y' parameter - start year
        year_param = request.args.get('y')
        year = year_param or TennisEvent.Years[0]
    except ValueError:
        year_param, year = None, TennisEvent.Years[0]
        log_info("Error: wrong main year (%s) -> setting %s" % (request.args.get('y'), year))

    try:  # 'm' parameter - max pictures; -1 for no limit
        max_pictures = int(request.args.get('m')) or 20
    except TypeError:
        max_pictures = 0
        log_info("Error: wrong max_pictures value (%s) -> setting %s" % (request.args.get('m'), max_pictures))
    except ValueError:
        max_pictures = 20
        log_info("Error: wrong max_pictures value (%s) -> setting %s" % (request.args.get('m'), max_pictures))
    param_m = request.args['m'] if 'm' in request.args else ''

    # 'a' parameter - collect all pictures, including do_not_show ones
    all_pictures = True if 'a' in request.args else False

    if year not in TennisEvent.Years:
        year_param, year = None, TennisEvent.Years[0]

    pictures = None
    next_y = year
    while not pictures:
        year = next_y
        pictures = TennisEvent.get_oneyear_pictures(year=year, max_pictures=max_pictures, all_pictures=all_pictures)
        next_y = TennisEvent.Years[TennisEvent.Years.index(year)+1]

    return render_template("pictures.html", pictures=pictures, year=year, param_m=param_m, param_a=all_pictures)


@app.route("/pictures_year", methods=['GET'])
def tennis_pictures_year():
    if request.method != 'GET':
        return

    try:
        year = request.args.get('y')
        if year not in TennisEvent.Years:
            year = TennisEvent.Years[0]
    except ValueError:
        year = TennisEvent.Years[0]
        log_info("Error: wrong main year (%s) -> setting %s" % (request.args.get('y'), year))

    try:  # 'm' parameter - max pictures; -1 for no limit
        max_pictures = int(request.args.get('m')) or 20
    except TypeError:
        max_pictures = 0
        log_info("Error: wrong max_pictures value (%s) -> setting %s" % (request.args.get('m'), max_pictures))
    except ValueError:
        max_pictures = 20
        log_info("Error: wrong max_pictures value (%s) -> setting %s" % (request.args.get('m'), max_pictures))
    param_m = request.args['m'] if 'm' in request.args else ''

    # 'a' parameter - collect all pictures, including do_not_show ones
    all_pictures = True if 'a' in request.args else False

    pictures, next_y = None, year
    while not pictures:
        year = next_y
        pictures = TennisEvent.get_oneyear_pictures(year=year, max_pictures=max_pictures, all_pictures=all_pictures)
        next_y = TennisEvent.Years[TennisEvent.Years.index(year)+1]

    return render_template("pictures_year.html", pictures=pictures, year=year, next_y=next_y,
                           param_m=param_m, param_a=all_pictures)


@app.route("/files", methods=['GET', 'POST'])
@login_required
def list_files():
    if request.method == 'GET':
        year = request.args.get('y') or TennisEvent.Years[0]
        search = request.args.get('s', '')
        try:
            files_filter = re.compile(r"%s" % search) if search else None
            log_info("Search pattern %s" % str(files_filter))
        except re.error:
            log_info("Error: re.error in list_files/re.compile")
            flash("Napaka pri nizu za iskanje")
            return redirect(request.args.get("next") or url_for("list_files"))
        except:
            log_info("Error: list_files/re.compile: %s" % sys.exc_info()[0])
            raise

        files = []
        for (y, fname, fsize, refs) in TennisEvent.sources:
            if (not files_filter and (y == year)) or (files_filter and files_filter.match(fname)):
                files.append((y, fname, fsize, refs))
        try:
            i = TennisEvent.Years.index(year)
        except ValueError:
            log_info("Error: ValueError in list_files/TennisEvent.Years.index for year %s" % year)
            i = 0

        prev_page = TennisEvent.Years[i-1] if i > 0 else TennisEvent.Years[0]
        next_page = TennisEvent.Years[i+1] if i < len(TennisEvent.Years)-1 else TennisEvent.Years[-1]
        return render_template("listFiles.html", files=files, search=search, years=TennisEvent.Years,
                               prevPage=prev_page, nextPage=next_page)

    elif request.method == 'POST':
        year = request.form.get('select_year', None) or TennisEvent.Years[0]
        search = request.form.get('search')
        return redirect(url_for("list_files", y=year, s=search))


@app.route("/editFile", methods=['GET', 'POST'])
@login_required
def edit_file():
    if request.method == 'GET':
        fname = request.args.get('n')
        fsize = "%d kB" % math.trunc(os.path.getsize(os.path.join(files_dir_os, fname)) / 1024)
        events = TennisEvent.get_events_with_att(fname)
        src = EventSource.get(os.path.join(fname[:4], fname[5:]))  # Todo: od klicu sestavim z '/', ne glede na OS
        title = src['desc'] if src else ""
        view = src['view'] if src and src in ['0', '1'] else "1"
        # log_info("view=%s." % view)
        players = src['players_on_pic'] if src else ""
        return render_template("editFile.html", year=fname[:4], fname=fname[5:], fsize=fsize,
                               years=TennisEvent.Years, events=events, title=title, view=view, players=players)
    elif request.method == 'POST':
        old_year, old_fname = request.form['old_year'], request.form['old_fname']
        new_year = secure_filename(request.form.get('new_year') or old_year)
        new_fname = secure_filename(request.form['new_fname'])
        old_title, new_title = request.form['old_title'], request.form['new_title']
        old_view, new_view = request.form['old_view'], request.form['new_view']
        old_players, new_players = request.form['old_players'], request.form['new_players']
        old_att = os.path.join(files_dir_os, old_year, old_fname)
        new_att = os.path.join(files_dir_os, new_year, new_fname)

        if request.form["Status"][:5] == unicode("Popravi"[:5]):
            log_info("Audit: rename file %s/%s to %s/%s" % (old_year, old_fname, new_year, new_fname))
            os.rename(old_att, new_att)
            TennisEvent.update_all_atts(old_year, old_fname, new_fname)
            # ToDo: delete old entry, if necessary (year | file_name changes)
            s = EventSource(file_name=os.path.join(new_year, new_fname),
                            desc=new_title, view=new_view, players_on_pic=new_players)
            s.update()
        elif request.form["Status"][:5] == unicode("Kopiraj"[:5]):
            log_info("Audit: copy file %s/%s to %s/%s" % (old_year, old_fname, new_year, new_fname))
            shutil.copyfile(old_att, new_att)

        return redirect(request.args.get("next") or url_for("tennis_events_old"))


@app.route("/upload_file", methods=['GET', 'POST'])
@login_required
def upload_picture():
    if request.method == 'GET':
        years = [request.args.get('y')] if request.args.get('y') else TennisEvent.Years
        files = []
        if len(years) == 1:
            dir_files = os.path.join(files_dir_os, secure_filename(years[0]))
            try:
                files = [f for f in os.listdir(dir_files) if allowed_file(f)]
            except OSError:
                files = []
            files.sort()
        return render_template("uploadFile.html", years=years, files=files)
    elif request.method == 'POST':
        if request.form["Status"] == "Shrani":
            year = request.form['select_year']
            upload_file = request.files.get('upload')
            select_name = request.form.get('select_name')
            new_name = request.form['new_name']
            if not upload_file:
                flash(u"NAPAKA: Napačno ime datoteke za prenos.")
                return redirect(url_for("upload_picture"))
            elif not allowed_file(upload_file.filename):
                flash(u"NAPAKA: Neustrezna vrsta datoteke.")
                return redirect(url_for("upload_picture"))
            elif select_name != "" and new_name != "":
                flash(u"NAPAKA: Nastavi le Obstoječe ime ALI Spremeni ime.")
                return redirect(url_for("upload_picture"))
            else:
                log_info("Temp: Upload %s, %s, %s" % (upload_file.filename, select_name, new_name))
                picture_dir = os.path.join(files_dir_os, secure_filename(year))
                if not os.path.exists(picture_dir):
                    log_info("Audit: directory %s created." % picture_dir)
                    os.makedirs(picture_dir)
                if select_name and select_name != "izberi":
                    save_name = secure_filename(select_name)
                elif new_name != "":
                    save_name = secure_filename(new_name)
                else:
                    save_name = secure_filename(upload_file.filename)
                log_info("Temp: Saving file: %s" % save_name)
                picture = os.path.join(picture_dir, save_name)
                upload_file.save(picture)
                log_info("Audit: picture %s uploaded." % picture)
                flash(u"Datoteka uspešno prenešena.")
        return redirect(request.args.get("next") or url_for("tennis_events_old"))


@app.route("/deleteFile", methods=['GET', 'POST'])
@login_required
def delete_file():
    if request.method == 'GET':
        fname = request.args.get('n')
        return render_template("deleteFile.html", fname=fname)
    elif request.method == 'POST':
        if request.form["Status"][:5] == unicode("Izbriši"[:5]):
            fname = os.path.join(secure_filename(request.form['Year']), secure_filename(request.form['Fname']))
            log_info("Audit: delete file %s" % fname)
            os.remove(os.path.join(files_dir_os, fname))
        return redirect(request.args.get("next") or url_for("tennis_events_old"))


# User functions
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
            user = User(username=u['Username'], pw_hash=u['Pw_hash'], ident=u['Ident'])
            if user and user.is_authenticated() and user.check_password(password):
                login_user(user, remember=remember_me)
                session['user'] = user.username
                log_info("Audit: User %s login." % user.username)
                flash(u"Prijava uspešna.")
                return redirect(request.args.get('next') or url_for("tennis_events_old"))

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
        failed = False
        if not valid_email(username):
            failed = True
            flash(u"Neustrezno uporabniško ime.")
        if not valid_password(pass1):
            failed = True
            flash(u"Neustrezno geslo.")
        if pass1 != pass2:
            failed = True
            flash(u"Geslo se ne ujema.")
        if not failed:
            user = User.get_by_user(username)
            if user is not None:
                failed = True
                flash(u"Uporabnik že obstaja.")
        if failed:
            return render_template("signup.html", username=username, password=pass1, verify=pass2)

        user = User(username=username, password=pass1)
        user.put()
        login_user(user)
        session['user'] = None
        log_info("Audit: New user %s created." % user.username)
        flash(u"Kreiran in prijavljen nov uporabnik.")
        return redirect(request.args.get("next") or url_for("tennis_events_old"))


@app.route("/logout")
@login_required
def logout():
    log_info("Audit: User %s logout." % str(current_user.username))
    logout_user()
    session.pop('user', None)
    flash(u"Odjava uspešna.")
    return redirect(request.args.get("next") or url_for("tennis_events_old"))


@app.route("/editUser", methods=['GET', 'POST'])
@login_required
def edit_user():
    if request.method == 'GET':
        if 'id' in request.args:
            try:
                iden = int(request.args.get('id'))
            except ValueError:
                log_info("Error: wrong edit_user identifier (%s)" % request.args.get('id'))
                flash(u"Napaka: edit_user - napačen identifikator.")
                return redirect(request.args.get("next") or url_for("tennis_events_old"))

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


@app.route("/events.zip", methods=['GET'], endpoint="events.zip", defaults={'action': 'events', 'fmt': 'zip'})
@app.route("/events.csv", methods=['GET'], endpoint="events.csv", defaults={'action': 'events', 'fmt': 'csv'})
@app.route("/people.csv", methods=['GET'], endpoint="people.csv", defaults={'action': 'people', 'fmt': 'csv'})
@app.route("/events.json", methods=['GET'], endpoint="events.json", defaults={'action': 'events', 'fmt': 'json'})
@app.route("/people.json", methods=['GET'], endpoint="people.json", defaults={'action': 'people', 'fmt': 'json'})
@login_required
def export(action, fmt):
    if request.method == 'GET':
        log_info("Audit: Data export (%s,%s) by %s." % (action, fmt, str(current_user.username)))
        if action == 'events':
            if fmt == "json":
                return TennisEvent.export('J')
            elif fmt == "csv":
                return TennisEvent.export('C')
            elif fmt == "zip":
                return TennisEvent.export('Z')
        elif action == 'people':
            if fmt == "json":
                return TennisPlayer.jsonify()


@app.route("/stat", methods=['GET'])
def stat():
    log_info("STAT")
    out = "Dogodkov: %d,\nIgralcev: %d\n, Virov: %d" % \
          (len(TennisEvent.EventsCache), len(TennisEvent.players), len(TennisEvent.sources))
    return Response(out, mimetype='text/plain')


@app.route("/audit", methods=['GET'])
@login_required
def audit():
    out = ""
    for log_file in sorted(glob.glob(LOG_FILE+"*"), reverse=True):
        out += ("\r\nLOG_FILE: %s\r\n" % log_file)
        with open(log_file, 'r') as f:
            for l in f:
                if l[30:37] != "Audit: ":
                    continue
                p = string.find(l, ' [', 37)
                out += "%s %s\r\n" % (l[:16], l[37:p])
        f.close()
    return Response(out, mimetype='text/plain')


@app.route("/shutdown", methods=['GET', 'POST'])
@login_required
def shutdown():
    if request.method == 'GET':
        log_info("Audit: System shutdown requested by %s." % str(current_user.username))
        return render_template("shutdown.html")
            
    elif request.method == 'POST':
        if request.form["Status"] == "Ugasni":
            log_info("Audit: System shutdown confirmed and executed")
            os.system("sudo shutdown -h 0")
        flash(u"Če je bilo ugašanje uspešno, stran ne bo več dosegljiva. :-)")
        return redirect(request.args.get("next") or url_for("tennis_events_old"))


if __name__ == "__main__":
    if Production:
        log_info("Audit: %s - start standalone production" % appname)
        TennisEvent.fetch_data()
        app.run(host='127.0.0.1', port=8080, debug=False)
    else:        
        log_info("Audit: %s - start standalone development" % appname)
        app.run(host='127.0.0.1', port=80, debug=True)
else:
    log_info("Audit: %s - Start" % appname)

# running 4 times, if max-procs=4 in fastcgi
TennisEvent.fetch_data()

log_info("Audit: %s - Initialized" % appname)