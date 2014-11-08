import string
import re
import csv

from Utils import app

from TennisData import TennisEvent

from flask import render_template, request, redirect, url_for
from werkzeug import secure_filename


att_ext = [".pdf",".PDF",".jpg",".JPG",".xls"]
def convertEntry( row ):
    entry = {}
    lastCol = 13
    while (row[lastCol] == "") and lastCol > 1:
        lastCol -= 1
    if lastCol >= 2:
        entry["date"] = unicode("00.00.%04s" % (row[0]))
        entry["event"] = unicode(row[1], "utf-8")
        m = re.search("^(\d{1,2})\.(\d{1,2})\.(\d{2,4})\s*", row[1])
        if m:
            entry["date"] = unicode("%02d.%02d.%04d" % (int(m.group(1)),int(m.group(2)),int(m.group(3))))
        entry["event"] = unicode(row[1][m.end():], "utf-8")
        entry["place"] = unicode(row[2], "utf-8")
        entry["category"] = unicode(row[3], "utf-8")
        entry["result"] = unicode(row[4], "utf-8")
        entry["player"] = unicode(string.strip(row[5]), "utf-8")
        entry["playerBirth"] = unicode(row[6], "utf-8")
        entry["comment"] = unicode("")
        entry["att1"] = unicode(string.strip(row[7]), "utf-8")
        if entry["att1"] != "" and not any(x in entry["att1"] for x in att_ext):
            entry["comment"] += entry["att1"] + "; "
            entry["att1"] = ""
        entry["att2"] = unicode(string.strip(row[8]), "utf-8")
        if entry["att2"] != "" and not any(x in entry["att2"] for x in att_ext):
            entry["comment"] += entry["att2"] + "; "
            entry["att2"] = ""
        entry["att3"] = unicode(string.strip(row[9]), "utf-8")
        if entry["att3"] != "" and not any(x in entry["att3"] for x in att_ext):
            entry["comment"] += entry["att3"] + "; "
            entry["att3"] = ""
        entry["att4"] = unicode(string.strip(row[10]), "utf-8")
        if entry["att4"] != "" and not any(x in entry["att4"] for x in att_ext):
            entry["comment"] += entry["att4"] + "; "
            entry["att4"] = ""
        

        return True, entry
    else:
        return False, None


'''
generate data from Execel: Export to text (Unicode)
convert to UTF-8
'''
@app.route('/Upload', methods=['GET', 'POST'])
def UploadCSV():
    if request.method == 'GET':
        return render_template("uploadFile.html")
    elif request.method == 'POST':
        line = 0
        f_upload = request.files['file']
        local_fname = "static/files/" + secure_filename(f_upload.filename)
        #f_upload.save( local_fname )
        with open(local_fname, 'rb') as csvfile:
            stringReader = csv.reader(csvfile,delimiter="\t",quotechar='"')
            for row in stringReader:
                line += 1
                if line == 1:
                    continue
                #logging.error("Row: %s" % (row) )
                (ok, entry) = convertEntry( row )
                #logging.error("Entry: %s - %s" % (str(ok), entry))
                if ok:
                    if line % 20 == 0:
                        app.logger.info( "IMPORT l.%d: %s - %s" % (line, entry['date'], entry['event']))
                    e = TennisEvent( date=entry["date"], event=entry["event"],
                                     place=entry["place"], category=entry["category"],
                                     result=entry["result"], player=entry["player"],
                                     comment=entry["comment"], att1=entry["att1"],
                                     att2=entry["att2"], att3=entry["att3"], att4=entry["att4"])
                    e.put()
        return redirect(url_for("TennisMain"))
