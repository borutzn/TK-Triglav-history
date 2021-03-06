# -*- coding: utf-8 -*-

# SQLite commands
#   .databases
#   .schema TennisPlayer


from config import DB_NAME, PAGELEN

import datetime
import re
import os
import sys
import json
import math
import random
import zipfile

import sqlite3

from flask import Response, make_response, send_file
from flask_login import current_user
from werkzeug.utils import secure_filename

from Utils import log_info, base_dir, files_dir_os, files_dir_web, UnicodeCsvWriter, allowed_image


class TennisEvent:
    """
    DROP TABLE TennisEvents;
    CREATE TABLE TennisEvents( Id INTEGER PRIMARY KEY, Date TEXT, Event TEXT,
            Place TEXT, Category TEXT, Result TEXT, Player TEXT, Comment TEXT,
            Att1 TEXT, Att2 TEXT, Att3 TEXT, Att4 TEXT, Source TEXT, Created DATE, LastModified DATE);
    DELETE FROM TennisEvents;
    """

    EventsCache = []  # type: list(dict)
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
        self.atts = {}
        self.att1 = att1
        self.att2 = att2
        self.att3 = att3
        self.att4 = att4
        self.source = source
        self.created = datetime.datetime.now()
        self.last_modified = self.created

    def __unicode__(self):
        return("TennisEvent [date=%s, event=%s, place=%s, category=%s, result=%s, player=%s, comment=%s,\
                att1=%s, att2=%s, att3=%s, att4=%s, source=%s, created=%s, modified=%s]" %
               (self.date, self.event, self.place, self.category, self.result, self.player, self.comment,
                self.att1, self.att2, self.att3, self.att4, self.source, self.created, self.last_modified))

    @classmethod
    def correct_att(cls, year, att):
        if att == "":
            return ""
            
        s = list(att)
        att = "".join(s)
        try:
            att_path = os.path.join(files_dir_os, year, att)
            att_sec = secure_filename(att)
            att_path_sec = os.path.join(files_dir_os, year, att_sec)
            if os.path.exists(att_path):  # or os.path.exists(att_path_sec):
                '''
                if att != att_sec: # correction of all unsecured attachments
                    TennisEvent.update_all_atts(year, att, att_sec)
                    log_info("Error: Unsecured filename %s" % att_path)
                    if not os.path.exists(att_path_sec):
                        log_info("AUDIT: rename file %s/%s to %s" % (year, att, att_path_sec))
                        os.rename(att_path, att_path_sec)
                '''
                return att_sec
            elif os.path.exists(att_path_sec):
                TennisEvent.update_all_atts(year, att, att_sec)
                return att_sec
            else:  # or os.path.exists(att_path_sec):
                log_info("Error: Bad filename " + unicode(os.path.join(files_dir_os, year + "/" + att)))
                return "err_"+att
        except (OSError, IOError) as e:
            log_info("OS errror: %s" % str(e))
        except:
            log_info("error: %s" % sys.exc_info()[0])

    @classmethod
    def date2user(cls, date):
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
            return d
        match = re.search(r"(\d{1,2})\.(\d{4})", d)
        if match:
            d = "%04d/%02d/%02d" % (int(match.group(2)), int(match.group(1)), 0)
            return d
        match = re.search(r"(\d{4})", d)
        if match:
            d = "%04d/%02d/%02d" % (int(match.group(1)), 0, 0)
            return d
                
        return "1900/01/01"

    def put(self, fetch=True):
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
        # self.clear_data()
        if fetch:
            self.fetch_data(force=True, sources=False)
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
        # self.clear_data()
        self.fetch_data(force=True, sources=False)

    def update_comment(self, iden):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        cursor.execute("""UPDATE TennisEvents SET Comment=:Comment, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                       {'Comment': self.comment, 'Id': iden})
        connection.commit()
        # self.clear_data()
        self.fetch_data(force=True, sources=False)

    @classmethod
    def update_att(cls, iden, att, fname):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        if type(att) != type(str):
            att = str(att)
        log_info("AUDIT: Event %s attachment update by %s." % (iden, str(current_user.username)))
        if att == "1":
            cursor.execute("""UPDATE TennisEvents SET Att1=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                           {'fname': fname, 'Id': iden})
        elif att == "2":
            cursor.execute("""UPDATE TennisEvents SET Att2=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                           {'fname': fname, 'Id': iden})
        elif att == "3":
            cursor.execute("""UPDATE TennisEvents SET Att3=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                           {'fname': fname, 'Id': iden})
        elif att == "4":
            cursor.execute("""UPDATE TennisEvents SET Att4=:fname, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""",
                           {'fname': fname, 'Id': iden})
        connection.commit()
        # ToDo: popravi tako, da se raje spremeni v cache-u, namesto: self.clear_data() -- ta hip ni nič!!
                
    @classmethod
    def update_all_atts(cls, old_year, old_att, new_att):
        for ev in cls.EventsCache:
            if ev['Date'][:4] != old_year:
                continue
            if ev['Att1'] == old_att:
                cls.update_att(ev['Id'], "1", new_att)
            if ev['Att2'] == old_att:
                cls.update_att(ev['Id'], "2", new_att)
            if ev['Att3'] == old_att:
                cls.update_att(ev['Id'], "3", new_att)
            if ev['Att4'] == old_att:
                cls.update_att(ev['Id'], "4", new_att)
        return

    @classmethod
    def delete(cls, iden):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        log_info("AUDIT: Event %s deleted by %s." % (iden, str(current_user.username)))
        cursor.execute("""DELETE FROM TennisEvents WHERE Id=:Id""", {'Id': iden})
        connection.commit()
        # cls.clear_data()
        cls.fetch_data(force=True, sources=False)

    @classmethod
    def fetch_data(cls, force=False, players=True, sources=True):
        if force:
            cls.EventsCache = []
        if cls.EventsCache:
            return

        log_info("AUDIT: Event cache - events reload started.")
        connection = sqlite3.connect(DB_NAME)
        with connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS TennisEvents( Id INTEGER PRIMARY KEY, Date TEXT, Event TEXT,"
                           "Place TEXT, Category TEXT, Result TEXT, Player TEXT, Comment TEXT, "
                           "Att1 TEXT, Att2 TEXT, Att3 TEXT, Att4 TEXT, Source TEXT, Created DATE, LastModified DATE)")
            cursor.execute("SELECT * FROM TennisEvents ORDER by Date, Event, Place, Category, Result")
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
        log_info("Audit: Event cache - events reloaded.")

        log_info("Audit: Event cache - players reload started.")
        if players:
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
            log_info("Audit: Event cache - players reloaded.")

        log_info("Audit: Event cache - sources reload started.")
        if sources:
            # ToDo: implement with os.scandir, when switching to Python 3
            cls.sources = list()
            year_pattern = re.compile(r"^[/\\]\d{4}$")
            dir_len = len(files_dir_os)
            try:
                for root, dirs, fnames in os.walk(files_dir_os):
                    year = root[dir_len:]  # year includes '/' in pos 0, because of the regex search
                    if year_pattern.match(year):
                        for fname in fnames:
                            fsize = "%d kB" % \
                                    math.trunc(os.path.getsize(os.path.join(files_dir_os, year[1:], fname))/1024)
                            no_events = len(TennisEvent.get_events_with_att(os.path.join(year[1:], fname)))
                            cls.sources.append((year[1:], fname, fsize, no_events))
            except ValueError:  # No files in directory - nothing to select from
                log_info("Error: ValueError in list_files/os.walk")
                pass

            cls.sources.sort()
            log_info("Audit: Event cache - sources reloaded.")

        log_info("Audit: Event cache reloaded (%d entries, %d players, %d sources)." %
                 (len(cls.EventsCache), len(cls.players), len(cls.sources)))

#    @classmethod
#    def clear_data(cls):
#        TennisEvent.EventsCache = []  # lazy approach - clear cache & reload again

    @classmethod
    def get(cls, iden):
        cls.fetch_data()
        idx = cls.EventsIndex[iden]
        return cls.EventsCache[idx]

    @classmethod
    def get_year_pos(cls, year):
        if not year:
            return 0
        cls.fetch_data()
        for idx, val in enumerate(cls.EventsCache):
            if val['Date'][:4] == year:
                return idx
        return 0

    @classmethod
    def get_events_page(cls, start, page_len=PAGELEN, event_filter=""):
        cls.fetch_data()
        events = list()
        pos = start-1
        search = 0  # 0-no search, 1-string, 2-regex

        if event_filter != "":
            search = 1 if event_filter.isalnum() else 2
            log_info("Temp: Search=" + str(search))
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
    def get_events_by_year(cls, year, event_filter=""):
        log_info("Temp: GET_BY_YEAR "+str(year)+", "+event_filter)
        cls.fetch_data()
        events = list()
        pos = TennisEvent.get_year_pos(year)
        search = 0  # 0-no search, 1-string, 2-regex

        if event_filter != "":
            search = 1 if event_filter.isalnum() else 2
            log_info("Temp: Search=" + str(search))
        try:
            search_pattern = re.compile(r"%s" % event_filter)
        except re.error:
            search, search_pattern = 1, event_filter
            log_info("Error: re.error in get_events_page/re.compile - changed to string")

        while pos < len(cls.EventsCache):
            if year is not None and cls.EventsCache[pos]['Date'][:4] > year:
                break
            if (search == 1) and (event_filter not in cls.EventsCache[pos]['Event']):
                pos += 1
                continue
            if (search == 2) and not search_pattern.match(cls.EventsCache[pos]['Event']):
                pos += 1
                continue
            events.append(cls.EventsCache[pos])
            pos += 1
        return events

    @classmethod
    def get_oneyear_events(cls, year=None, player=None, event_filter=""):
        cls.fetch_data()
        events = list()
        pos = TennisEvent.get_year_pos(year)
        search = 0  # 0-no search, 1-string, 2-regex

        if event_filter != "":
            search = 1 if event_filter.isalnum() else 2
            log_info("Temp: Search=" + str(search))
        try:
            search_pattern = re.compile(r"%s" % event_filter)
        except re.error:
            search, search_pattern = 1, event_filter
            log_info("Error: re.error in get_events_page/re.compile - changed to string")

        to_year = None
        prev_entry, prev_group = None, False
        gr_start = 0  # should not be necessary, only because of the pycharm messages
        while pos < len(cls.EventsCache):
            # log_info("found " + str(cls.EventsCache[pos]['Event']))
            if to_year and (cls.EventsCache[pos]['Date'][:4] > to_year):
                break

            if player and (cls.EventsCache[pos]['Player'] != player):
                pos += 1
                continue
            if (search == 1) and (event_filter not in cls.EventsCache[pos]['Event']):
                pos += 1
                continue
            if (search == 2) and not search_pattern.match(cls.EventsCache[pos]['Event']):
                pos += 1
                continue

            entry = cls.EventsCache[pos]
            curr_grp = 0
            # izračunati moramo, kateri entry pomeni na podlagi trenutnega in prejšnjega entrya
            # 1 - začetek grupe,  2 - sredina grupe,  3 - konec grupe
            if not prev_entry:  # the first entry
                group = False
            else:
                group = prev_entry['Date'] == entry['Date'] and prev_entry['Event'] == entry['Event'] and \
                        prev_entry['Place'] == entry['Place']
                if not prev_group:  # ni še grupe
                    if group:  # začetek grupe
                        gr_start = len(events)-1
                        events[gr_start][0] = 1  # set previous entry to 'start group'
                        events[gr_start][1]['atts'] = \
                            {prev_entry['Att1'], prev_entry['Att2'], prev_entry['Att3'], prev_entry['Att4']}
                        curr_grp = 2
                else:  # nadaljevanje grupe
                    if group:  # nadaljevanje grupe
                        curr_grp = 2
                        events[gr_start][1]['atts'].update(
                            {prev_entry['Att1'], prev_entry['Att2'], prev_entry['Att3'], prev_entry['Att4']})
                    else:  # konec grupe
                        events[-1][0] = 3  # set previous entry to 'end group'

            events.append([curr_grp, entry])
            if not to_year:
                to_year = entry['Date'][:4]
            prev_entry = entry
            prev_group = group
            pos += 1

        if events and events[-1][0] == 2:  # last element = mid-group --> end-group
            events[-1][0] = 3
        log_info("Temp: GET_EVENTS returning %d events." % len(events))
        return events

    @classmethod
    def get_oneyear_pictures(cls, year=None, max_pictures=7, all_pictures=False, max_years=1):
        """
        Get pictures for one year
        :param year: selected year; random year is selected, if not defined
        :param max_pictures: maxsimum number of pictures to collect or all if <= 0
        :param all_pictures: collect also do_not_show pictures, if True
        :param max_years: maximum number of years to check, if starting year doesn't have enough pictures
        :return: list of pictures in format (path, title, path, show)
        """
        cls.fetch_data()
        pictures, no_pics = list(), 0
        no_year = not year or (year == 0)

        if no_year:
            year = TennisEvent.Years[random.randint(0, len(TennisEvent.Years)-1)]
        for _ in range(max_years):  # check up to 'loops' consecutive years to fill the 'limit_size' pictures
            for (file_year, file_name, file_size, references) in cls.sources:
                if (references > 0) and (file_year == year) and allowed_image(file_name):
                    pic_data = EventSource.get(os.path.join(file_year, file_name))
                    if pic_data:
                        title = pic_data['desc']
                        if pic_data['players_on_pic'] != '':
                            title += ' (' + pic_data['players_on_pic'] + ')'
                    else:
                        title = file_name
                    if all_pictures or not pic_data or (pic_data and pic_data['view'] != 0):
                        pictures.append((os.path.join(files_dir_web, file_year, file_name), title,
                                         os.path.join(file_year, file_name),
                                         pic_data['view'] if pic_data else 0))
            no_pics = len(pictures)
            i = TennisEvent.Years.index(year)
            if (no_pics >= max_pictures) or (i >= len(TennisEvent.Years)-1):
                break
            if no_year:
                r = random.randint(0, len(TennisEvent.Years)-1)
                year = TennisEvent.Years[r]
            else:
                year = TennisEvent.Years[i+1]

        if max_pictures > 0:
            for _ in range(no_pics-max_pictures):
                r = random.randrange(0, no_pics)
                del pictures[r]
                no_pics -= 1
        random.shuffle(pictures)

        log_info("Temp: get_oneyear_pictures: got {} pictures for {}.".format(len(pictures), year))
        return pictures

    @classmethod
    def get_oneplayer_pictures(cls, player="", limit_size=7):
        cls.fetch_data()
        pictures = set()

        for entry in cls.EventsCache:
            if entry['Player'] != player:
                continue
            year = entry['Date'][:4]
            if entry['Att1'] and entry['Att1'][:4] != "err_" and allowed_image(entry['Att1']):
                pictures.add((os.path.join(files_dir_web, year, entry['Att1']), entry['Att1']))
            if entry['Att2'] and entry['Att2'][:4] != "err_" and allowed_image(entry['Att2']):
                pictures.add((os.path.join(files_dir_web, year, entry['Att2']), entry['Att2']))
            if entry['Att3'] and entry['Att3'][:4] != "err_" and allowed_image(entry['Att3']):
                pictures.add((os.path.join(files_dir_web, year, entry['Att3']), entry['Att3']))
            if entry['Att4'] and entry['Att4'][:4] != "err_" and allowed_image(entry['Att4']):
                pictures.add((os.path.join(files_dir_web, year, entry['Att4']), entry['Att4']))
        pictures = list(pictures)

        no_pics = len(pictures)
        for _ in range(no_pics - limit_size):
            r = random.randrange(0, no_pics)
            del pictures[r]
            no_pics -= 1
        random.shuffle(pictures)

        log_info("Temp: get_oneplayer_pictures: got %d pictures for {}.".format(len(pictures), player))
        return pictures

    @classmethod
    def get_players_events(cls, player, no_records=None):
        cls.fetch_data()
        r = list()
        for ev in cls.EventsCache:
            if ev['Player'] == player:
                r.append(ev)
                if no_records and (no_records >= len(r)):
                    break
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
                for root, dirs, fnames in os.walk(files_dir_os):
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
    DELETE FROM TennisPlayer;
    """

    PlayersCache = []  # type: list(dict)
    PlayersIndex = {}

    def __init__(self, name, born="", died="", comment="", picture=""):
        self.Name = name
        self.Born = born
        self.Died = died
        self.Comment = comment
        self.Picture = picture

    def update(self):
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()

        log_info("Audit: Player %s update by %s." % (self.Name, str(current_user.username)))
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
    def fetch_data(cls):
        if cls.PlayersCache:  # is not None
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

        log_info("Audit: Players cache reloaded (%d entries)." % len(cls.PlayersCache))

    @classmethod
    def clear_data(cls):
        TennisPlayer.PlayersCache = []  # lazy approach - clear cache & reload again

    @classmethod
    def get(cls, name):
        cls.fetch_data()
        if name in cls.PlayersIndex:
            idx = cls.PlayersIndex[name]
            return cls.PlayersCache[idx]
        else:
            log_info(u"Error: TennisPlayer.get: {} not found".format(name))
            # # ToDo: correct!! log_info(u"Error: TennisPlayer.get: ?? not found")
            return None

    @classmethod
    def jsonify(cls):
        return Response(json.dumps(cls.PlayersCache), mimetype='application/json')


class EventSource:
    """
    DROP TABLE EventSource;
    DELETE FROM EventSource;
    """

    SourcesCache = []  # type: list(dict)
    SourcesIndex = {}

    def __init__(self, file_name, desc="", view=1, players_on_pic=""):
        self.file_name = file_name
        self.desc = desc
        self.view = view
        self.players_on_pic = players_on_pic

    def update(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        log_info("Audit: Source %s update by %s." % (self.file_name, str(current_user.username)))
        cursor.execute("""CREATE TABLE IF NOT EXISTS EventSource(
                            file_name TEXT PRIMARY KEY, desc TEXT, view INTEGER, players_on_pic TEXT);""")
        cursor.execute("""INSERT OR REPLACE INTO EventSource(file_name, desc, view, players_on_pic)
                            VALUES (:File_name, :Desc, :View, :Players_on_pic)""",
                       {"File_name": self.file_name, "Desc": self.desc, "View": self.view,
                        "Players_on_pic": self.players_on_pic})
        conn.commit()
        self.clear_data()
        return cursor.lastrowid

    @classmethod
    def fetch_data(cls):
        if cls.SourcesCache:
            return

        connection = sqlite3.connect(DB_NAME)
        with connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            # cursor.execute("DROP TABLE EventSource")
            cursor.execute("""CREATE TABLE IF NOT EXISTS EventSource(
                                file_name TEXT PRIMARY KEY, desc TEXT, view INTEGER, players_on_pic TEXT);""")
            cursor.execute("SELECT * FROM EventSource")
            cls.SourcesCache = [dict(row) for row in cursor]
            connection.commit()

        for idx, val in enumerate(cls.SourcesCache):
            cls.SourcesIndex[val['file_name']] = idx

        log_info("Audit: Sources cache reloaded (%d entries)." % len(cls.SourcesCache))

    @classmethod
    def clear_data(cls):
        EventSource.SourcesCache = []  # lazy approach - clear cache & reload again

    @classmethod
    def get(cls, fname):
        cls.fetch_data()
        if fname in cls.SourcesIndex:
            # log_info("EventSrc: found %s in %s" % (fname, cls.SourcesCache))
            idx = cls.SourcesIndex[fname]
            # log_info("EventSrc: found %d, %s" % (idx, cls.SourcesCache[idx]))
            return cls.SourcesCache[idx]
        else:
            # ToDo: attachments are inserted into DB only when title, view is changed.
            # Maybe, I should automatically add them here?
            log_info("Info: EventSrc.get: file {} not yet in DB".format(fname))
            return None

    @classmethod
    def delete(cls, fname):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        log_info("Audit: Source %s deleted by %s." % (fname, str(current_user.username)))
        cursor.execute("""DELETE FROM EventSource WHERE file_name=:Fname""", {'Fname': fname})
        connection.commit()
        cls.clear_data()
        cls.fetch_data()
