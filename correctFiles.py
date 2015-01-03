#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
program by Borut Žnidar on 12.12.2014
"""

from config import DbName, FILES_BASEDIR

import os
import difflib
import sqlite3

responseCache = {}


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
    filename, fit = "", 0.0
    for f in os.listdir(FILES_BASEDIR+"/"+y):
        newfit = difflib.SequenceMatcher(None, att, f).ratio()
        if newfit > fit:
            filename, fit = f, newfit
    # print( "%s (%d%%)" % (fname, 100*fit) )
    return filename, fit


def check_att(y, att):
    if att == "":
        return False
    if os.path.exists(os.path.join(FILES_BASEDIR, y, att)):
        return False
    return True


def update_entry(iden, num, att):
    conn = sqlite3.connect(DbName)
    curs = conn.cursor()
    if num == 1:
        curs.execute("""UPDATE TennisEvents SET Att1=:att, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""", {'att': att, 'Id': iden})
    elif num == 2:
        curs.execute("""UPDATE TennisEvents SET Att2=:att, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""", {'att': att, 'Id': iden})
    elif num == 3:
        curs.execute("""UPDATE TennisEvents SET Att3=:att, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""", {'att': att, 'Id': iden})
    elif num == 4:
        curs.execute("""UPDATE TennisEvents SET Att4=:att, LastModified=CURRENT_TIMESTAMP WHERE Id=:Id""", {'att': att, 'Id': iden})
    conn.commit()                


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
delete = raw_input("Delete all data from TennisEvents (y/n)?")
if delete == "y":
    print("-> Data deleted")
    conn = sqlite3.connect(DbName)
    curs = conn.cursor()
    curs.execute("DELETE FROM TennisEvents")
    conn.commit()

print
print("STEP 2: Importing data")


print
print("STEP 2: Translating filenames from Windows-1250 to UTF-8")
changed_files = 0
try:
    for root, directory, files in os.walk(FILES_BASEDIR):
        print("DIR: " + str(root))
        for fname in files:
            if check_file(root, fname):
                changed_files += 1
except ValueError:  # No files in directory - nothing to select from
    pass        


print
print("STEP 3: correcting attachements in the DB")
changed_atts = 0
conn = sqlite3.connect(DbName)
with conn:
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    curs.execute("SELECT * FROM TennisEvents ORDER by date")
    EventsCache = [dict(row) for row in curs]
    conn.commit()

for row in EventsCache:
    ident = row["Id"]
    year = row["Date"][:4]
    if check_att(year, row["Att1"]):
        changed_atts += update_att(ident, 1, year, row["Att1"])
    if check_att(year, row["Att2"]):
        changed_atts += update_att(ident, 2, year, row["Att2"])
    if check_att(year, row["Att3"]):
        changed_atts += update_att(ident, 3, year, row["Att3"])
    if check_att(year, row["Att4"]):
        changed_atts += update_att(ident, 4, year, row["Att4"])

    print
    print("STEP 4: resizing oversized pictures")
    for ext in ('JPG', 'jpg'):
        cmd = "mogrify -resize 500 %s/*/*.%s" % (FILES_BASEDIR, ext)
        print("  run: %s" % cmd)
        os.system(cmd)

    print("-------------------------")
    print("SUMMARY: %d files changed; %d attachements changed" % (changed_files, changed_atts))
