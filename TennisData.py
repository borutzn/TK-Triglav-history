from config import DB_NAME, PAGELEN

import datetime
import re
import os
import sys
import json
import math
import zipfile

import sqlite3

from flask import url_for, Response, make_response, send_file
from flask_login import current_user
from werkzeug.utils import secure_filename

from Utils import log_info, base_dir, files_dir, UnicodeCsvWriter


class TennisEvent:
    """
    DROP TABLE TennisEvents;
    CREATE TABLE TennisEvents( Id INTEGER PRIMARY KEY, Date TEXT, Event TEXT,
            Place TEXT, Category TEXT, Result TEXT, Player TEXT, Comment TEXT,
            Att1 TEXT, Att2 TEXT, Att3 TEXT, Att4 TEXT, Source TEXT, Created DATE, LastModified DATE);
    DELETE FROM TennisEvents;
    """

    EventsCache = None
    EventsIndex = {}
    Years = []
    players = list()
    top_players = list()
    sources = list()

    def __init__(self, date="", event="", place="", category="", result="",
                 player="", comment="", att1="", att2="", att3="", att4="", source=""):
        self.date = date
        self.event = event
        self.place = place
        self.category = category
        self.result = result
        self.player = player
        self.comment = comment
        self.att1 = att1
        self.att2 = att2
        self.att3 = att3
        self.att4 = att4
        self.source = source
        self.created = datetime.datetime.now()
        self.last_modified = self.created

    @classmethod
    def result_value(cls, v):
        if v.isnumeric():
            return 4-int(v) if int(v) < 4 else 0
        return 0
        
    @classmethod
    def get_fname(cls, year, att):
        return url_for('static', filename="files/" + year + "/" + year + "_" + att)
        
    @classmethod
    def correct_att(cls, year, att):
        if att == "":
            return ""
            
        s = list(att)
        att = "".join(s)
        try:
            att_path = os.path.join(files_dir, year, att)
            att_sec = secure_filename(att)
            att_path_sec = os.path.join(files_dir, year, att_sec)
            if os.path.exists(att_path):  # or os.path.exists(att_path_sec):
                '''
                if att != att_sec: # correction of all unsecured attachments
                    TennisEvent.update_all_atts(year, att, att_sec)
                    log_info("ERROR: Unsecured filename %s" % att_path)
                    if not os.path.exists(att_path_sec):
                        log_info("AUDIT: rename file %s/%s to %s" % (year, att, att_path_sec))
                        os.rename(att_path, att_path_sec)
                '''
                return att_sec
            elif os.path.exists(att_path_sec):
                TennisEvent.update_all_atts(year, att, att_sec)
                return att_sec
            else:  # or os.path.exists(att_path_sec):
                log_info("ERROR: Bad filename " + unicode(os.path.join(files_dir, year+"/"+att)))
                return "err_"+att
        except:
            log_info("ERROR: unknown error %s" % sys.exc_info()[0])

    @classmethod
    def date2user(cls, date):
        # log_info( "date2user from : "+str(type(date))+", "+str(date) )
        match = re.search(r"(\d{4})/(\d{0,2})/?(\d{0,2})", date)
        if match:
            (d, m, y) = (int(match.group(3)), int(match.group(2)), int(match.group(1)))
            if d == 0 and m == 0:
                return "%04d" % y
            elif d == 0:
                return "%02d.%04d" % (m, y)
            else:
                return "%02d.%02d.%04d" % (d, m, y)
        return "00.00.0000"

    @classmethod
    def date2db(cls, d):
        match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", d)
        if match:
            d = "%04d/%02d/%02d" % (int(match.group(3)), int(match.group(2)), int(match.group(1)))
            # log_info("date2Db to: "+str(d))
            return d
        match = re.search(r"(\d{1,2})\.(\d{4})", d)
        if match:
            d = "%04d/%02d/%02d" % (int(match.group(2)), int(match.group(1)), 0)
            # log_info("date2Db to: "+str(d))
            return d
        match = re.search(r"(\d{4})", d)
        if match:
            d = "%04d/%02d/%02d" % (int(match.group(1)), 0, 0)
            # log_info("date2Db to: "+str(d))
            return d
                
        return "1900/01/01"

    def put(self):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        log_info("AUDIT: New event put by %s" % (str(current_user.username)))
        cursor.execute("""INSERT INTO TennisEvents
                       (Date,Event,Place,Category,Result,Player,Comment,Att1,Att2,Att3,Att4,Source,Created,LastModified)
                        VALUES (:Date, :Event, :Place, :Category, :Result, :Player, :Comment, :Att1, :Att2, :Att3,
                        :Att4, :Source, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                       {"Date": TennisEvent.date2db(self.date), "Event": self.event, "Place": self.place,
                        "Category": self.category, "Result": self.result, "Player": self.player,
                        "Comment": self.comment, "Att1": self.att1, "Att2": self.att2, "Att3": self.att3,
                        "Att4": self.att4, "Source": self.source})
        connection.commit()
        self.clear_data()
        return cursor.lastrowid

    def update(self, iden):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        log_info("AUDIT: Event %s update by %s." % (iden, str(current_user.username)))
        cursor.execute("""UPDATE TennisEvents SET Date=:Date, Event=:Event, Place=:Place, Category=:Category,
                        Result=:Result, Player=:Player, Comment=:Comment, Att1=:Att1, Att2=:Att2, Att3=:Att3,
                        Att4=:Att4, Source=:Source, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                       {'Id': iden, 'Date': TennisEvent.date2db(self.date), 'Event': self.event, 'Place': self.place,
                        'Category': self.category, 'Result': self.result, 'Player': self.player,
                        'Comment': self.comment, 'Att1': self.att1, 'Att2': self.att2, 'Att3': self.att3,
                        'Att4': self.att4, 'Source': self.source})
        connection.commit()
        self.clear_data()
                
    def update_comment(self, iden):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        cursor.execute("""UPDATE TennisEvents SET Comment=:Comment, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                       {'Comment': self.comment, 'Id': iden})
        connection.commit()
        self.clear_data()
                
    @classmethod
    def update_att(cls, iden, att, fname):
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()

        if type(att) != type(str):
            att = str(att)
        log_info("AUDIT: Event %s attachment update by %s." % (iden, str(current_user.username)))
        if att == "1":
            curs.execute("""UPDATE TennisEvents SET Att1=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                         {'fname': fname, 'Id': iden})
        elif att == "2":
            curs.execute("""UPDATE TennisEvents SET Att2=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                         {'fname': fname, 'Id': iden})
        elif att == "3":
            curs.execute("""UPDATE TennisEvents SET Att3=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                         {'fname': fname, 'Id': iden})
        elif att == "4":
            curs.execute("""UPDATE TennisEvents SET Att4=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                         {'fname': fname, 'Id': iden})
        conn.commit()
        # ToDo: popravi tako, da se raje spremeni v cache-u, namesto: self.clear_data()
                
    @classmethod
    def update_all_atts(cls, old_year, old_att, new_att):
        for ev in cls.EventsCache:
            if ev['Date'][:4] != old_year:
                continue
            if ev['Att1'] == old_att:
                log_info("CHANGE ATT1 id=%d, %s -> %s" % (ev['Id'], ev['Att1'], new_att))
                cls.update_att(ev['Id'], "1", new_att)
            if ev['Att2'] == old_att:
                log_info("CHANGE ATT2 id=%d, %s -> %s" % (ev['Id'], ev['Att2'], new_att))
                cls.update_att(ev['Id'], "2", new_att)
            if ev['Att3'] == old_att:
                log_info("CHANGE ATT3 id=%d, %s -> %s" % (ev['Id'], ev['Att3'], new_att))
                cls.update_att(ev['Id'], "3", new_att)
            if ev['Att4'] == old_att:
                log_info("CHANGE ATT4 id=%d, %s -> %s" % (ev['Id'], ev['Att4'], new_att))
                cls.update_att(ev['Id'], "4", new_att)
        return

    @classmethod
    def delete(cls, iden):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        log_info("AUDIT: Event %s deleted by %s." % (iden, str(current_user.username)))
        cursor.execute("""DELETE FROM TennisEvents WHERE Id=:Id""", {'Id': iden})
        connection.commit()
        cls.clear_data()
                
    @classmethod
    def fetch_data(cls):
        if cls.EventsCache is not None:
            return
            
        connection = sqlite3.connect(DB_NAME)
        with connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS TennisEvents( Id INTEGER PRIMARY KEY, Date TEXT, Event TEXT, "
                           "Place TEXT, Category TEXT, Result TEXT, Player TEXT, Comment TEXT, "
                           "Att1 TEXT, Att2 TEXT, Att3 TEXT, Att4 TEXT, Source TEXT, Created DATE, LastModified DATE)")
            cursor.execute("SELECT * FROM TennisEvents ORDER by Date, Event, Category, Result")
            cls.EventsCache = [dict(row) for row in cursor]
            connection.commit()

        cls.years = []
        for idx, val in enumerate(cls.EventsCache):
            cls.EventsCache[idx]['LocalDate'] = cls.date2user(val['Date'])
            cls.EventsCache[idx]['Att1'] = cls.correct_att(val['Date'][:4], val['Att1'])
            cls.EventsCache[idx]['Att2'] = cls.correct_att(val['Date'][:4], val['Att2'])
            cls.EventsCache[idx]['Att3'] = cls.correct_att(val['Date'][:4], val['Att3'])
            cls.EventsCache[idx]['Att4'] = cls.correct_att(val['Date'][:4], val['Att4'])
            cls.EventsIndex[val['Id']] = idx
            year = val['Date'][:4]
            if year not in cls.Years:
                cls.Years.append(year)
        cls.Years.sort()

        p = dict()  # move collection to the upper for loop?
        for i in cls.EventsCache:
            p_name = i['Player']
            if p_name in p:
                p[p_name] += 1
            else:
                p[p_name] = 1
        cls.players = list()
        cls.top_players = list()
        for k, v in p.iteritems():
            cls.players.append(k)
            cls.top_players.append((k, v))
        cls.players.sort()
        cls.top_players.sort(key=lambda player: player[1], reverse=True)
        cls.top_players = cls.top_players[:20]

        sources = []
        year_pattern = re.compile(r"^/\d{4}$")
        dir_len = len(files_dir)
        try:
            for root, dirs, fnames in os.walk(files_dir):
                year = root[dir_len:]
                if year_pattern.match(year):
                    for fname in fnames:
                        fsize = "%d kB" % math.trunc(os.path.getsize(os.path.join(files_dir, year[1:], fname))/1024)
                        events = len(TennisEvent.get_events_with_att(fname))
                        sources.append((year[1:], fname, fsize, events))
        except ValueError:  # No files in directory - nothing to select from
            log_info("Error: ValueError in list_files/os.walk")
            pass
        log_info( "SOURCE: %s" % str(sources))

        log_info("AUDIT: Event cache reloaded (%d entries, %d players, %d sources)." %
                 (len(cls.EventsCache), len(cls.players), len(cls.sources)))

    @classmethod
    def clear_data(cls):
        TennisEvent.EventsCache = None  # lazy approach - clear cache & reload again

    @classmethod
    def get(cls, iden):
        cls.fetch_data()
        idx = cls.EventsIndex[iden]
        return cls.EventsCache[idx]

    @classmethod
    def get_year_pos(cls, year):
        cls.fetch_data()
        for idx, val in enumerate(cls.EventsCache):
            if val['Date'][:4] == year:
                return idx
        return 0

    @classmethod
    def get_events_page(cls, start, page_len=PAGELEN, event_filter="", collapsed_groups=()):
        cls.fetch_data()
        events = list()
        pos = start-1
        search = 0  # 0-no search, 1-string, 2-regex

        if event_filter != "":
            search = 1 if event_filter.isalnum() else 2
            log_info("SEARCH=" + str(search))
        try:
            search_pattern = re.compile(r"%s" % event_filter)
        except re.error:
            search, search_pattern = 1, event_filter
            log_info("Error: re.error in get_events_page/re.compile - changed to string")

        while (len(events) < page_len) and (pos < len(cls.EventsCache)-1):
            pos += 1
            if (search == 1) and (event_filter not in cls.EventsCache[pos]['Event']):
                continue
            if (search == 2) and not search_pattern.match(cls.EventsCache[pos]['Event']):
                continue
            events.append(cls.EventsCache[pos])
        return events

    @classmethod
    def get_players_events(cls, player):
        cls.fetch_data()
        r = list()
        for ev in cls.EventsCache:
            if ev['Player'] == player:
                r.append(ev)
        return r

    @classmethod
    def get_events_with_att(cls, att):
        cls.fetch_data()
        r = list()
        att_year = att[:4]
        att = att[5:]
        for ev in cls.EventsCache:
            if ev['Date'][:4] != att_year:
                continue
            if (ev['Att1'] == att) or (ev['Att2'] == att) or (ev['Att3'] == att) or (ev['Att4'] == att):
                r.append("%s - %s" % (ev['LocalDate'], ev['Event']))
        return r

    @classmethod
    def count(cls):
        cls.fetch_data()
        return len(cls.EventsCache)

    @classmethod
    def export(cls, typ):
        export_rows = ['Date', 'Event', 'Place', 'Category', 'Result', 'Player', 'Comment', 'Att1', 'Att2', 'Att3',
                       'Att4', 'Source']
        if typ == 'J':
            return Response(json.dumps(cls.EventsCache), mimetype='application/json')
        elif typ == 'C':
            csv_out = UnicodeCsvWriter(delimiter=';', quotechar='"')
            out = csv_out.convert_row(export_rows)
            for ev in cls.EventsCache:
                out += csv_out.convert_row([ev['Date'], ev['Event'], ev['Place'], ev['Category'], ev['Result'],
                                            ev['Player'], ev['Comment'], ev['Att1'], ev['Att2'], ev['Att3'],
                                            ev['Att4'], ev['Source']])
            response = make_response(out)
            response.headers["Content-Disposition"] = "attachment; filename=books.csv"
            return response
        elif typ == 'Z':
            timestamp = datetime.datetime.now().strftime('%d.%m.%Y')
            zip_name = 'TK-Triglav-History-' + str(timestamp) + '.zip'
            # TODO: create new file
            zip_file = zipfile.ZipFile(os.path.join(base_dir, zip_name), 'w')
            zip_file.write(os.path.join(base_dir, "TennisHistory.db"), "TennisHistory.db")
            try:
                for root, dirs, fnames in os.walk(files_dir):
                    for f in fnames:
                        zip_file.write(os.path.join(root, f), os.path.join(root[len(base_dir):], f))
            except ValueError:
                pass
            zip_file.close()
            # TODO: remove zipped files

            return send_file(zip_name, attachment_filename=zip_name, as_attachment=True)


class TennisPlayer:
    """
    DROP TABLE TennisPlayer;
    CREATE TABLE TennisPlayer( Ident INTEGER PRIMARY KEY, Name TEXT, Born INTEGER, Died INTEGER,
            Comment TEXT, Picture TEXT, Created DATE, LastModified DATE);
    DELETE FROM TennisPlayer;
    """

    PlayersCache = None
    PlayersIndex = {}

    def __init__(self, name, born="", died="", comment="", picture=""):
        self.Name = name
        self.Born = born
        self.Died = died
        self.Comment = comment
        self.Picture = picture

    @classmethod
    def fetch_data(cls):
        if cls.PlayersCache is not None:
            return
            
        connection = sqlite3.connect(DB_NAME)
        with connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS TennisPlayer( Name TEXT PRIMARY KEY, Born INTEGER,
                           Died INTEGER, Comment TEXT, Picture TEXT, Created DATE, LastModified DATE )""")
            cursor.execute("SELECT * FROM TennisPlayer")
            cls.PlayersCache = [dict(row) for row in cursor]
            connection.commit()

        for idx, val in enumerate(cls.PlayersCache):
            cls.PlayersIndex[val['Name']] = idx

        # app.logger.error( "CACHE " + str(cls.PlayersCache) )
        # app.logger.error( "CACHE " + str(cls.PlayersIndex) )
        log_info("AUDIT: Players cache reloaded (%d entries)." % len(cls.PlayersCache))

    @classmethod
    def clear_data(cls):
        TennisPlayer.PlayersCache = None  # lazy approach - clear cache & reload again

    @classmethod
    def get(cls, name):
        cls.fetch_data()
        if name in cls.PlayersIndex:
            # app.logger.error( "GET " + Name )
            idx = cls.PlayersIndex[name]
            # app.logger.error( "GET " + str(idx) )
            # app.logger.error( "return " + str(cls.PlayersCache[idx]) )
            return cls.PlayersCache[idx]
        else:
            return None

    def update(self):
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()

        log_info("AUDIT: Player %s update by %s." % (self.Name, str(current_user.username)))
        curs.execute("""CREATE TABLE IF NOT EXISTS TennisPlayer( Name TEXT PRIMARY KEY, Born INTEGER, Died INTEGER,
                     Comment TEXT, Picture TEXT, Created DATE, LastModified DATE )""")
        curs.execute("""INSERT OR REPLACE INTO TennisPlayer (Name, Born, Died, Comment, Picture, Created,LastModified)
                     VALUES (:Name, :Born, :Died, :Comment, :Picture, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                     {"Name": self.Name, "Born": self.Born, "Died": self.Died,
                      "Comment": self.Comment, "Picture": self.Picture})
        conn.commit()
        self.clear_data()
        return curs.lastrowid

    @classmethod
    def jsonify(cls):
        return Response(json.dumps(cls.PlayersCache),  mimetype='application/json')