import os
import sqlite3
from optparse import OptionParser

# Setting up the option parser
parser = OptionParser()

parser.add_option("-l", "--level", dest="level", type="str")
parser.add_option("-p", "--part", dest="part", type="str")
parser.add_option("-t", "--type", dest="type", type="str")

(options, args) = parser.parse_args()

files = []
for file in os.listdir("data"):
    level, part, type_ = file.split("-")[:3]
    if level == options.level and part == options.part and type_ == options.type:
        files.append(file)

DBNAME = "{}-{}-{}-complete.sqlite".format(options.level, options.part, options.type)
DBDIR = "data"

conn = sqlite3.connect(os.path.join(DBDIR, DBNAME))
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS Record')

cursor.execute('''CREATE TABLE Record 
    (id INTEGER UNIQUE NOT NULL, idx INTEGER NOT NULL, rollno INTEGER NOT NULL, html TEXT NOT NULL, 
     error BOOLEAN NOT NULL)''')

counter = 1
for file in files:
    print("Processing file: {}".format(file))
    file_conn = sqlite3.connect(os.path.join(DBDIR, file))
    file_cursor = file_conn.cursor()
    file_cursor.execute('''SELECT idx, rollno, html, error FROM Record''')
    data = file_cursor.fetchall()
    for row in data:
        cursor.execute('INSERT INTO Record VALUES (?, ?, ?, ?, ?)', (counter, row[0], row[1], row[2], row[3]))
        counter += 1
        if counter % 1000 == 0:
            conn.commit()
            print("Thousand more records committed. Total Records: {}".format(counter * 1000))
    conn.commit()
    file_conn.close()

conn.close()
