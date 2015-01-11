#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
program by Borut Žnidar on 12.12.2014
"""

from config import DB_NAME, ATT_EXT

import os
import re
import sys
import csv
import string
import difflib
import sqlite3

from TennisData import TennisEvent, TennisPlayer

from Utils import log_info


files_basedir = os.path.join(os.path.dirname(__file__), 'static', 'files')

responseCache = {}


""" CSV fields structure
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
"""


def convert_entry(row):
    entry = {}
    last_col = 13
    while (row[last_col] == "") and last_col > 1:
        last_col -= 1
    if last_col >= 2:
        r = re.search("^(\d{1,2})\.(\d{1,2})\.(\d{2,4})", row[0])
        if r:
            (d, m, y) = (int(r.group(1)), int(r.group(2)), int(r.group(3)))
            entry["date"] = unicode("%02d.%02d.%04d" % (d, m, y))
        else:
            (d, m, y) = (0, 0, int(row[0]))
            entry["date"] = unicode("%02d.%02d.%04s" % (d, m, y))
        entry["event"] = unicode(row[2], "utf-8")
        entry["place"] = unicode(row[3], "utf-8")
        sex = unicode(row[4], "utf-8")
        doubles = "dvojice" if unicode(row[5], "utf-8") != "" else ""
        category = unicode(row[6], "utf-8")
        entry["category"] = "%s %s %s" % (sex, category, doubles)
        entry["result"] = unicode(row[7], "utf-8")
        entry["player"] = unicode(string.strip(row[8]), "utf-8")
        r = re.search("\((\d{1,2})\)$", entry["player"])
        if r:
            entry["playerBorn"] = "19" + r.group(1)
            entry["player"] = entry["player"][:-5]
        else:
            entry["playerBorn"] = ""
        entry["comment"] = unicode("")
        if row[1] == '*':
            entry["comment"] = u"vnešen datum vira; "
        entry["att1"] = unicode(string.strip(row[9]), "utf-8")
        if entry["att1"] != "" and not any(x in entry["att1"] for x in ATT_EXT):
            entry["comment"] += entry["att1"] + "; "
            entry["att1"] = ""
        if entry["att1"] != "":
            if d == 0 and m == 0:
                entry["att1"] = "%d_%s" % (y, entry["att1"])
            else:
                entry["att1"] = "%d.%d.%d_%s" % (y, m, d, entry["att1"])

        entry["att2"] = unicode(string.strip(row[10]), "utf-8")
        if entry["att2"] != "" and not any(x in entry["att2"] for x in ATT_EXT):
            entry["comment"] += entry["att2"] + "; "
            entry["att2"] = ""
        if entry["att2"] != "":
            if d == 0 and m == 0:
                entry["att2"] = "%d_%s" % (y, entry["att2"])
            else:
                entry["att2"] = "%d.%d.%d_%s" % (y, m, d, entry["att2"])

        entry["att3"] = unicode(string.strip(row[11]), "utf-8")
        if entry["att3"] != "" and not any(x in entry["att3"] for x in ATT_EXT):
            entry["comment"] += entry["att3"] + "; "
            entry["att3"] = ""
        if entry["att3"] != "":
            if d == 0 and m == 0:
                entry["att3"] = "%d_%s" % (y, entry["att3"])
            else:
                entry["att3"] = "%d.%d.%d_%s" % (y, m, d, entry["att3"])

        entry["att4"] = unicode(string.strip(row[12]), "utf-8")
        if entry["att4"] != "" and not any(x in entry["att4"] for x in ATT_EXT):
            entry["comment"] += entry["att4"] + "; "
            entry["att4"] = ""
        if entry["att4"] != "":
            if d == 0 and m == 0:
                entry["att4"] = "%d_%s" % (y, entry["att4"])
            else:
                entry["att4"] = "%d.%d.%d_%s" % (y, m, d, entry["att4"])

        return True, entry
    else:
        return False, None


def check_file(file_root, file_name):
    new_file_name = ""
    for c in file_name:
        if ord(c) <= 128:
            new_file_name += c
        elif ord(c) == 138:
            new_file_name += 'Š'
        elif ord(c) == 142:
            new_file_name += 'Ž'
        elif ord(c) == 154:
            new_file_name += 'š'
        elif ord(c) == 158:
            new_file_name += 'ž'
        else:
            print(ord(c))

    if file_name == new_file_name:
        return False

    os.rename(os.path.join(file_root, file_name), os.path.join(root, new_file_name))
    return True


def get_best_filename(y, att):
    best_filename, fit = "", 0.0
    for f in os.listdir(files_basedir+"/"+y):
        newfit = difflib.SequenceMatcher(None, att, f).ratio()
        if newfit > fit:
            best_filename, fit = f, newfit
    # print( "%s (%d%%)" % (fname, 100*fit) )
    return best_filename, fit


def check_att(y, att):
    if att == "":
        return False
    if os.path.exists(os.path.join(files_basedir, y, att)):
        return False
    return True


def update_entry(iden, num, att):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    if num == 1:
        cursor.execute("""UPDATE TennisEvents SET Att1=:att, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""", {'att': att, 'Id': iden})
    elif num == 2:
        cursor.execute("""UPDATE TennisEvents SET Att2=:att, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""", {'att': att, 'Id': iden})
    elif num == 3:
        cursor.execute("""UPDATE TennisEvents SET Att3=:att, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""", {'att': att, 'Id': iden})
    elif num == 4:
        cursor.execute("""UPDATE TennisEvents SET Att4=:att, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""", {'att': att, 'Id': iden})
    connection.commit()


def update_att(iden, num, y, att):
    (new_att, fit) = get_best_filename(y, att)
    if att in responseCache:
        # print( "FOUND" + str(responseCache[att]) )
        change = responseCache[att][0]
        if change == "y":
            change = "a"
    elif fit >= 0.84:
        change = "a"
    elif fit < 0.70:
        change = "n"
    else:
        print("%d:     %s" % (num, att))
        print("  %d%%  %s" % (100*fit, new_att))
        change = raw_input("   Change (y/n)?")
        responseCache[att] = (change, new_att)
    if change == "y" or change == "a":
        update_entry(iden, num, new_att)
        if change == "y":
            print("-> Att changed")
        else:
            print("(%d%%) %s -> %s" % (100*fit, att, new_att))
        return 1
    return 0


print
print("STEP 1: Clearing database")
delete = raw_input("Delete all data from TennisEvents (y/n)? ")
if delete == "y":
    print("-> Data deleted")
    conn = sqlite3.connect(DB_NAME)
    curs = conn.cursor()
    curs.execute("DELETE FROM TennisEvents")
    conn.commit()

print
print("STEP 2: Importing data")
"""
    - generate data from Execel: Export to text (Unicode)
    - convert to UTF-8
"""

line = 0
if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = raw_input("Input filename ("" for no)? ")
if filename != "":
    print("  importing from %s" % filename)
    with open(filename, 'rb') as csvfile:
        string_reader = csv.reader(csvfile, delimiter="\t", quotechar='"')
        for row in string_reader:
            line += 1
            if line == 1:
                continue
            # log_info("Row: %s" % (row) )
            (ok, entry) = convert_entry(row)
            # log_info("Entry: %s - %s" % (str(ok), entry))
            if ok:
                if line % 20 == 0:
                    log_info("IMPORT l.%d: %s - %s" % (line, entry['date'], entry['event']))
                ev = TennisEvent(date=entry["date"], event=entry["event"], place=entry["place"],
                                 category=entry["category"], result=entry["result"],
                                 player=entry["player"], comment=entry["comment"],
                                 att1=entry["att1"], att2=entry["att2"], att3=entry["att3"], att4=entry["att4"])
                ev.put()
                if entry["player"] != "" and entry["playerBorn"] != "":
                    pl = TennisPlayer(name=entry["player"], born=entry["playerBorn"])
                    pl.update()


print
print("STEP 3: Translating filenames from Windows-1250 to UTF-8")
changed_files = 0
try:
    for root, directory, files in os.walk(files_basedir):
        print("DIR: " + str(root))
        for fname in files:
            if check_file(root, fname):
                changed_files += 1
except ValueError:  # No files in directory - nothing to select from
    pass        


print
print("STEP 4: correcting attachements in the DB")
changed_atts = 0
conn = sqlite3.connect(DB_NAME)
with conn:
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    curs.execute("SELECT * FROM TennisEvents ORDER by date")
    EventsCache = [dict(row) for row in curs]
    conn.commit()

for row in EventsCache:
    iden = row["Id"]
    year = row["Date"][:4]
    if check_att(year, row["Att1"]):
        changed_atts += update_att(iden, 1, year, row["Att1"])
    if check_att(year, row["Att2"]):
        changed_atts += update_att(iden, 2, year, row["Att2"])
    if check_att(year, row["Att3"]):
        changed_atts += update_att(iden, 3, year, row["Att3"])
    if check_att(year, row["Att4"]):
        changed_atts += update_att(iden, 4, year, row["Att4"])

print
print("STEP 5: resizing oversized pictures")
mogrify = raw_input("Mogrify the pictures (y/n)? ")
if delete == "y":
    for ext in ATT_EXT:
        cmd = "mogrify -resize 500 %s/*/*%s" % (files_basedir, ext)
        print("  run: %s" % cmd)
        os.system(cmd)

print("-------------------------")
print("SUMMARY: %d files changed; %d attachements changed" % (changed_files, changed_atts))
