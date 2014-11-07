import datetime
import logging
import re
import os

import sqlite3


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
            return "static/files/" + year + "/" + year + "_" + att
        
        @classmethod
        def correctAtt( cls, year, att ):
            if att == "":
                return ""
            
            s = list(att)
            for i, c in enumerate(s):
                if ord(c) >= 128:
                    s[i] = "_"
            att = "".join(s)
            fname = "static/files/" + year + "/" + year + "_" + att
            #logging.error( "correct: " + str(fname) +" - "+ str(os.path.exists(fname)) )
            if os.path.exists(fname):
                return att
            else:
                return "err_"+att

                
        @classmethod
        def date2user( cls, date ):
                #logging.error( "date2user from : "+str(type(date))+", "+str(date) )
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

                logging.error( "PUT: "+str(self.date)+":"+str(TennisEvent.date2Db(self.date)) )
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

                logging.error("update"+str(Att))
                curs.execute( """UPDATE TennisEvents SET Att1=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                              { 'fname':fname, 'Id':Id, 'Att':Att } )
                conn.commit()                
                self.clearData()
                

        @classmethod
        def delete(self, Id):
                conn = sqlite3.connect(DbName)
                curs = conn.cursor()

                curs.execute( """DELETE FROM TennisEvents WHERE Id=:Id""", { 'Id':Id } )
                #logging.error("DELETE Id="+str(Id))
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
                curs.execute( "SELECT * FROM TennisEvents ORDER by date" )
                cls.EventsCache = [ dict(row) for row in curs ]
                conn.commit()

            for idx, val in enumerate(cls.EventsCache):
                cls.EventsCache[idx]['LocalDate'] = cls.date2user( cls.EventsCache[idx]['Date'] )
                cls.EventsCache[idx]['Att1'] = cls.correctAtt( cls.EventsCache[idx]['Date'][:4], cls.EventsCache[idx]['Att1'] )
                cls.EventsCache[idx]['Att2'] = cls.correctAtt( cls.EventsCache[idx]['Date'][:4], cls.EventsCache[idx]['Att2'] )
                cls.EventsCache[idx]['Att3'] = cls.correctAtt( cls.EventsCache[idx]['Date'][:4], cls.EventsCache[idx]['Att3'] )
                cls.EventsCache[idx]['Att4'] = cls.correctAtt( cls.EventsCache[idx]['Date'][:4], cls.EventsCache[idx]['Att4'] )
                cls.EventsIndex[val['Id']] = idx

            p = dict()
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

            logging.warning( "Cache reloaded (%d entries)" % len(cls.EventsCache) )

        @classmethod
        def clearData(cls):
                TennisEvent.EventsCache = None # lazy approach - clear cache & reload again


        @classmethod
        def get(cls, Id):
                cls.fetchData()                        
                idx = cls.EventsIndex[Id]
                return cls.EventsCache[idx]


        @classmethod
        def getEventsPage(cls, start, pagelen ):
                cls.fetchData()                        
                return cls.EventsCache[start:start+pagelen]               


        @classmethod
        def getPlayersEvents(cls, player ):
                cls.fetchData()
                r = list()
                for e in cls.EventsCache:
                        if e['player'] == player:
                                r.append( e )      
                return r


        @classmethod
        def count(cls ):
                cls.fetchData()           
                return len(cls.EventsCache)


