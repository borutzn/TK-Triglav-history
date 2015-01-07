from config import DB_NAME

import datetime
import re
import os
import json

import sqlite3

from flask import url_for, Response

from Utils import log_info, files_dir


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
        if os.path.exists(os.path.join(files_dir, year,att)):
            return att
        else:
            # log_info( "Bad filename: " + unicode(os.path.join(files_dir,year+"/"+att)) )
            return "err_"+att

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

        # log_info( "PUT: "+str(TennisEvent.date2Db(self.date)) + ": " + self.comment )
        cursor.execute("""INSERT INTO TennisEvents
                       (Date,Event,Place,Category,Result,Player,Comment,Att1,Att2,Att3,Att4,Created,LastModified)
                        VALUES (:Date, :Event, :Place, :Category, :Result, :Player, :Comment, :Att1, :Att2, :Att3,
                        :Att4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                       {"Date": TennisEvent.date2db(self.date), "Event": self.event, "Place": self.place,
                        "Category": self.category, "Result": self.result, "Player": self.player,
                        "Comment": self.comment, "Att1": self.att1, "Att2": self.att2, "Att3": self.att3,
                        "Att4": self.att4})
        connection.commit()
        self.clear_data()
        return cursor.lastrowid

    def update(self, iden):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        log_info("UPDATE %s" % str(iden))
        cursor.execute("""UPDATE TennisEvents SET Date=:Date, Event=:Event, Place=:Place, Result=:Result, Player=:Player,
                       Comment=:Comment, Att1=:Att1, Att2=:Att2, Att3=:Att3, Att4=:Att4, LastModified=CURRENT_TIMESTAMP
                       WHERE Id=:Id""",
                       {'Id': iden, 'Date': TennisEvent.date2db(self.date), 'Event': self.event, 'Place': self.place,
                        'Result': self.result, 'Player': self.player, 'Comment': self.comment,
                        'Att1': self.att1, 'Att2': self.att2, 'Att3': self.att3, 'Att4': self.att4})
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
            cursor.execute("SELECT * FROM TennisEvents ORDER by date")
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
            p_result = cls.result_value(i['Result'])
            if p_name in p:
                p[p_name][0] += 1
                p[p_name][1] += p_result
            else:
                p[p_name] = list((1, p_result))
        cls.players = list()
        for k, v in p.iteritems():
            cls.players.append((k, v[0], v[1]))
        cls.players.sort(key=lambda player: player[2], reverse=True)

        log_info("Event cache reloaded (%d entries)" % len(cls.EventsCache))

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
    def get_events_page(cls, start, pagelen):
        cls.fetch_data()
        return cls.EventsCache[start:start+pagelen]

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
    def jsonify(cls):
        #r = "".join( jsonify(ev) for ev in cls.EventsCache)
        #return "{ " + r + " }"
        return Response(json.dumps(cls.EventsCache),  mimetype='application/json')


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
        log_info("Players cache reloaded (%d entries)" % len(cls.PlayersCache))

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

        curs.execute("""CREATE TABLE IF NOT EXISTS TennisPlayer( Name TEXT PRIMARY KEY, Born INTEGER, Died INTEGER,
                     Comment TEXT, Picture TEXT, Created DATE, LastModified DATE )""")
        curs.execute("""INSERT OR REPLACE INTO TennisPlayer (Name, Born, Died, Comment, Picture, Created,LastModified)
                     VALUES (:Name, :Born, :Died, :Comment, :Picture, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                     {"Name": self.Name, "Born": self.Born, "Died": self.Died,
                      "Comment": self.Comment, "Picture": self.Picture})
        conn.commit()
        self.clear_data()
        return curs.lastrowid
