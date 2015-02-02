from config import DB_NAME, PAGELEN

import datetime
import re
import os
import sys
import json

import sqlite3

from flask import url_for, Response
from flask_login import current_user

from Utils import log_info, files_dir, UnicodeCsvWriter


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
            p = os.path.join(files_dir, year, att)
            if os.path.exists(p):
                return att
            else:
                # log_info( "Bad filename: " + unicode(os.path.join(files_dir,year+"/"+att)) )
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
        # popravi tako, da se raje spremeni v cache-u, namesto: self.clear_data()
                
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
            
        log_info("AUDIT: Event cache reload #1.")
        connection = sqlite3.connect(DB_NAME)
        with connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS TennisEvents( Id INTEGER PRIMARY KEY, Date TEXT, Event TEXT, "
                           "Place TEXT, Category TEXT, Result TEXT, Player TEXT, Comment TEXT, "
                           "Att1 TEXT, Att2 TEXT, Att3 TEXT, Att4 TEXT, Source TEXT, Created DATE, LastModified DATE)")
            cursor.execute("SELECT * FROM TennisEvents ORDER by date")
            cls.EventsCache = [dict(row) for row in cursor]
            connection.commit()

        log_info("AUDIT: Event cache reload #2.")
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

        log_info("AUDIT: Event cache reload #3.")
        p = dict()  # move collection to the upper for loop?
        for i in cls.EventsCache:
            p_name = i['Player']
            if p_name in p:
                p[p_name] += 1
            else:
                p[p_name] = 1
        log_info("AUDIT: Event cache reload #4. ")
        cls.players = list()
        cls.top_players = list()
        for k, v in p.iteritems():
            cls.players.append(k)
            cls.top_players.append((k, v))
        cls.players.sort()
        cls.top_players.sort(key=lambda player: player[1], reverse=True)
        cls.top_players = cls.top_players[:20]

        log_info("AUDIT: Event cache reloaded (%d entries, %d players)." % (len(cls.EventsCache), len(cls.players)))

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
        while (len(events) < page_len) and (pos < len(cls.EventsCache)-1):
            pos += 1
            if (search == 1) and (event_filter not in cls.EventsCache[pos]['Event']):
                continue
            if (search == 2) and not re.search(event_filter, cls.EventsCache[pos]['Event']):
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
"""
si = StringIO.StringIO()
cw = csv.writer(si)
for row in csvList:
    cw.writerow(row)
output = make_response(si.getvalue())
output.headers["Content-Disposition"] = "attachment; filename=export.csv"
output.headers["Content-type"] = "text/csv"
return output
"""
""" http://stackoverflow.com/questions/26513542/flask-how-to-send-a-dynamically-generate-zipfile-to-the-client
r = requests.post('http://ogre.adc4gis.com/convertJson', data = data)
if r.status_code == 200:
    return Response(r.content,
            mimetype='application/zip',
            headers={'Content-Disposition':'attachment;filename=zones.zip'})
"""


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