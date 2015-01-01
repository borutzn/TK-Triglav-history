import datetime
import logging
import re
import os

import sqlite3

from flask import url_for
#where from?? from __main__ import name

from Utils import app, log_info, files_dir


DbName = "TennisHistory.db"

'''
DROP TABLE TennisEvents;
CREATE TABLE TennisEvents( Id INTEGER PRIMARY KEY, Date TEXT, Event TEXT,
        Place TEXT, Category TEXT, Result TEXT, Player TEXT, Comment TEXT,
        Att1 TEXT, Att2 TEXT, Att3 TEXT, Att4 TEXT, Source TEXT, Created DATE, LastModified DATE);
DELETE FROM TennisEvents;
'''
class TennisEvent:

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
        def resultValue( cls, v ):
                if v.isnumeric():
                        return 4-int(v) if int(v)<4 else 0
                return 0
        
        @classmethod
        def getFname( cls, year, att ):
            return url_for('static', filename="files/" + year + "/" + year + "_" + att )
        
        @classmethod
        def correctAtt( cls, year, att ):
            if att == "":
                return ""
            
            s = list(att)
            att = "".join(s)
            if os.path.exists(os.path.join(files_dir,year+"/"+att)):
                return att
            else:
                # log_info( "Bad filename: " + unicode(os.path.join(files_dir,year+"/"+att)) )
                return "err_"+att

                
        @classmethod
        def date2user( cls, date ):
                #log_info( "date2user from : "+str(type(date))+", "+str(date) )
                match=re.search(r"(\d{4})/(\d{0,2})/?(\d{0,2})",date)
                if match:
                        (d,m,y) = (int(match.group(3)), int(match.group(2)), int(match.group(1)))
                        if d==0 and m==0:
                                return "%04d" % y
                        elif d==0:
                                return "%02d.%04d" % (m,y)
                        else:
                                return "%02d.%02d.%04d" % (d,m,y)
                return "00.00.0000"
        
        @classmethod
        def date2Db( cls, d ):
                match=re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})",d)
                if match:
                        d = "%04d/%02d/%02d" % (int(match.group(3)),int(match.group(2)),int(match.group(1)))
                        logging.error( "date2Db to: "+str(d) )
                        return d
                match=re.search(r"(\d{1,2})\.(\d{4})",d)
                if match:
                        d = "%04d/%02d/%02d" % (int(match.group(2)),int(match.group(1)),0)
                        logging.error( "date2Db to: "+str(d) )
                        return d
                match=re.search(r"(\d{4})",d)
                if match:
                        d = "%04d/%02d/%02d" % (int(match.group(1)),0,0)
                        logging.error( "date2Db to: "+str(d) )
                        return d
                
                return "1900/01/01"


        def put(self):
                conn = sqlite3.connect(DbName)
                curs = conn.cursor()

                #log_info( "PUT: "+str(TennisEvent.date2Db(self.date)) + ": " + self.comment )
                curs.execute( """INSERT INTO TennisEvents (Date,Event,Place,Category,Result,Player,Comment,Att1,Att2,Att3,Att4,Created,LastModified)
                                VALUES (:Date, :Event, :Place, :Category, :Result, :Player, :Comment, :Att1, :Att2, :Att3, :Att4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                                      {"Date":TennisEvent.date2Db(self.date), "Event":self.event, "Place":self.place, "Category":self.category,
                                       "Result":self.result, "Player":self.player, "Comment":self.comment,
                                       "Att1":self.att1, "Att2":self.att2, "Att3":self.att3, "Att4":self.att4} )
                conn.commit()
                self.clearData()
                return curs.lastrowid
                

        def update(self, Id):
                conn = sqlite3.connect(DbName)
                curs = conn.cursor()

                log_info( "UPDATE %s" % str(Id) )
                curs.execute( """UPDATE TennisEvents SET Date=:Date, Event=:Event, Place=:Place, Result=:Result,
                        Player=:Player, Comment=:Comment, Att1=:Att1, Att2=:Att2, Att3=:Att3, Att4=:Att4, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                              { 'Id':Id, 'Date':TennisEvent.date2Db(self.date), 'Event':self.event, 'Place':self.place,
                                'Result':self.result, 'Player':self.player, 'Comment':self.comment,
                                'Att1':self.att1, 'Att2':self.att2, 'Att3':self.att3, 'Att4':self.att4 } )
                conn.commit()                
                self.clearData()
                

        def updateComment(self, Id):
                conn = sqlite3.connect(DbName)
                curs = conn.cursor()

                curs.execute( """UPDATE TennisEvents SET Comment=:Comment, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                              { 'Comment':self.comment, 'Id':Id } )
                conn.commit()                
                self.clearData()
                

        @classmethod
        def updateAtt(self, Id, Att, fname):
                conn = sqlite3.connect(DbName)
                curs = conn.cursor()

                if Att == "1":
                    curs.execute( """UPDATE TennisEvents SET Att1=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                                  { 'fname':fname, 'Id':Id } )
                elif Att == "2":
                    curs.execute( """UPDATE TennisEvents SET Att2=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                                  { 'fname':fname, 'Id':Id } )
                elif Att == "3":
                    curs.execute( """UPDATE TennisEvents SET Att3=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                                  { 'fname':fname, 'Id':Id } )
                elif Att == "4":
                    curs.execute( """UPDATE TennisEvents SET Att4=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                                  { 'fname':fname, 'Id':Id } )
                conn.commit()                
                # popravi tako, da se raje spremeni v cache-u, namesto: self.clearData()
                

        @classmethod
        def delete(self, Id):
                conn = sqlite3.connect(DbName)
                curs = conn.cursor()

                curs.execute( """DELETE FROM TennisEvents WHERE Id=:Id""", { 'Id':Id } )
                conn.commit()                
                self.clearData()
                

        @classmethod
        def fetchData(cls):
            if cls.EventsCache != None:
                return
            
            conn = sqlite3.connect(DbName)
            with conn:
                conn.row_factory = sqlite3.Row
                curs = conn.cursor()
                curs.execute( "CREATE TABLE IF NOT EXISTS TennisEvents( Id INTEGER PRIMARY KEY, Date TEXT, Event TEXT, Place TEXT, Category TEXT, Result TEXT, Player TEXT, Comment TEXT, Att1 TEXT, Att2 TEXT, Att3 TEXT, Att4 TEXT, Source TEXT, Created DATE, LastModified DATE)" )
                curs.execute( "SELECT * FROM TennisEvents ORDER by date" )
                cls.EventsCache = [ dict(row) for row in curs ]
                conn.commit()

            cls.years = []
            for idx, val in enumerate(cls.EventsCache):
                cls.EventsCache[idx]['LocalDate'] = cls.date2user( cls.EventsCache[idx]['Date'] )
                cls.EventsCache[idx]['Att1'] = cls.correctAtt( cls.EventsCache[idx]['Date'][:4], cls.EventsCache[idx]['Att1'] )
                cls.EventsCache[idx]['Att2'] = cls.correctAtt( cls.EventsCache[idx]['Date'][:4], cls.EventsCache[idx]['Att2'] )
                cls.EventsCache[idx]['Att3'] = cls.correctAtt( cls.EventsCache[idx]['Date'][:4], cls.EventsCache[idx]['Att3'] )
                cls.EventsCache[idx]['Att4'] = cls.correctAtt( cls.EventsCache[idx]['Date'][:4], cls.EventsCache[idx]['Att4'] )
                cls.EventsIndex[val['Id']] = idx
                year = cls.EventsCache[idx]['Date'][:4]
                if not year in cls.Years:
                    cls.Years.append( year )
                    log_info( year + ":" + str(cls.Years) )

            p = dict() # move collection to the upper for loop?
            for i in cls.EventsCache:
                pName = i['Player']
                pResult = cls.resultValue(i['Result'])
                if pName in p:
                    p[pName][0] += 1
                    p[pName][1] += pResult
                else:
                    p[pName] = list( (1, pResult) )
            cls.players = list()
            for k, v in p.iteritems():
                cls.players.append( (k, v[0], v[1]) )
            cls.players.sort(key=lambda player: player[2], reverse=True)

            log_info( "Event cache reloaded (%d entries)" % len(cls.EventsCache) )

        @classmethod
        def clearData(cls):
            TennisEvent.EventsCache = None # lazy approach - clear cache & reload again


        @classmethod
        def get(cls, Ident):
            cls.fetchData()
            idx = cls.EventsIndex[Ident]
            return cls.EventsCache[idx]


        @classmethod
        def getYearPos(cls, year):
            cls.fetchData()
            log_info( "get Y pos: " + year )
            
            return 0


        @classmethod
        def getEventsPage(cls, start, pagelen ):
                cls.fetchData()                        
                return cls.EventsCache[start:start+pagelen]               


        @classmethod
        def getPlayersEvents(cls, player ):
            cls.fetchData()
            r = list()
            for e in cls.EventsCache:
                if e['Player'] == player:
                    r.append( e )      
            return r


        @classmethod
        def count(cls ):
            cls.fetchData()           
            return len(cls.EventsCache)



'''
DROP TABLE TennisPlayer;
CREATE TABLE TennisPlayer( Ident INTEGER PRIMARY KEY, Name TEXT, Born INTEGER, Died INTEGER, 
        Comment TEXT, Picture TEXT, Created DATE, LastModified DATE);
DELETE FROM TennisPlayer;
'''
class TennisPlayer:

        PlayersCache = None
        PlayersIndex = {}

        def __init__(self, Name, Born="", Died="", Comment="", Picture=""):
                self.Name = Name
                self.Born = Born
                self.Died = Died
                self.Comment = Comment
                self.Picture = Picture

        @classmethod
        def fetchData(cls):
            if cls.PlayersCache != None:
                return
            
            conn = sqlite3.connect(DbName)
            with conn:
                conn.row_factory = sqlite3.Row
                curs = conn.cursor()
                curs.execute( "CREATE TABLE IF NOT EXISTS TennisPlayer( Name TEXT PRIMARY KEY, Born INTEGER, Died INTEGER, Comment TEXT, Picture TEXT, Created DATE, LastModified DATE )" )
                curs.execute( "SELECT * FROM TennisPlayer" )
                cls.PlayersCache = [ dict(row) for row in curs ]
                conn.commit()

            for idx, val in enumerate(cls.PlayersCache):
                cls.PlayersIndex[val['Name']] = idx

            #app.logger.error( "CACHE " + str(cls.PlayersCache) )
            #app.logger.error( "CACHE " + str(cls.PlayersIndex) )
            app.logger.warning( "Players cache reloaded (%d entries)" % len(cls.PlayersCache) )


        @classmethod
        def clearData(cls):
                TennisPlayer.PlayersCache = None # lazy approach - clear cache & reload again


        @classmethod
        def get(cls, Name):
            cls.fetchData()                        
            if Name in cls.PlayersIndex:
                #app.logger.error( "GET " + Name )
                idx = cls.PlayersIndex[Name]
                #app.logger.error( "GET " + str(idx) )
                #app.logger.error( "return " + str(cls.PlayersCache[idx]) )
                return cls.PlayersCache[idx]
            else:
                return None

        def update(self):
                conn = sqlite3.connect(DbName)
                curs = conn.cursor()

                logging.error( "PUT " )
                curs.execute( "CREATE TABLE IF NOT EXISTS TennisPlayer( Name TEXT PRIMARY KEY, Born INTEGER, Died INTEGER, Comment TEXT, Picture TEXT, Created DATE, LastModified DATE )" )
                curs.execute( """INSERT OR REPLACE INTO TennisPlayer (Name, Born, Died, Comment, Picture, Created,LastModified)
                                VALUES (:Name, :Born, :Died, :Comment, :Picture, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                                      {"Name":self.Name, "Born":self.Born, "Died":self.Died,
                                       "Comment":self.Comment, "Picture":self.Picture} )
                conn.commit()                
                self.clearData()
                return curs.lastrowid
