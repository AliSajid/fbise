import os
from collections import defaultdict
from optparse import OptionParser

from bs4 import BeautifulSoup
from pony import orm

from cleanmodels import cleandb, Student, Result
from models import db, Record

# Setting up the option parser
parser = OptionParser()

parser.add_option("-l", "--level", dest="level", type="str")
parser.add_option("-p", "--part", dest="part", type="str")
parser.add_option("-t", "--type", dest="type", type="str")

(options, args) = parser.parse_args()

DBDIR = "data"
INPUTDBNAME = "{}-{}-{}-complete.sqlite".format(options.level, options.part, options.type)
OUTPUTDBNAME = "{}-{}-{}-clean.sqlite".format(options.level, options.part, options.type)

db.bind('sqlite', os.path.join(DBDIR, INPUTDBNAME))
db.generate_mapping()

cleandb.bind('sqlite', os.path.join(DBDIR, OUTPUTDBNAME), create_db=True)
cleandb.generate_mapping(create_tables=True)

with orm.db_session:
    test = orm.select(c for c in Record if c.error == 0)[:]


def split_tables(soup):
    info, results = soup.find_all('table')[-2:]
    return info, results


def parse_info(info_soup):
    d = defaultdict(str)
    for row in info_soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) == 2:
            d[cells[0].text.strip().upper()] = cells[1].text.strip()
    return d


def parse_results(result_soup):
    result_list = list()
    headers = [h.text.strip().upper() for h in result_soup.find_all('th')]
    for row in result_soup.find_all('tr'):
        result_row = defaultdict(str)
        cells = row.find_all('td')
        if len(cells) == 4:
            for idx, cell in enumerate(cells):
                result_row[headers[idx]] = cells[idx].text.strip()
            result_list.append(result_row)
    return result_list


soup = BeautifulSoup(test[0].html, 'lxml')
info, result = split_tables(soup)
info_p = parse_info(info)
res_p = parse_results(result)

@orm.db_session
def parse_and_store_result(html):
    soup = BeautifulSoup(html, 'lxml')
    info, result = split_tables(soup)
    parsed_info = parse_info(info)
    parsed_result = parse_results(result)
    student = Student(rollno=parsed_info["ROLL NO"], name=parsed_info["CANDIDATE NAME"],
                      father=parsed_info["FATHER  NAME"], institute=parsed_info["INSTITUTE"],
                      remarks=parsed_info["REMARKS"], result=parsed_info["RESULT"])
    for row in parsed_result:
        split = row["SUBJECTS"].split(" - ")
        if len(split) == 2:
            subj, part = split
        else:
            subj = row["SUBJECTS"].strip()
            part = ''
        if row["THEORY"] == "ABS":
            theory = 999
        elif row["THEORY"] == "CAN":
            theory = 998
        else:
            theory = int(row["THEORY"])

        if row["PRACTICAL"] == "ABS":
            practical = 999
        else:
            try:
                practical = int(row["PRACTICAL"])
            except ValueError:
                practical = None

        Result(student=student, subject=subj, part=part, theory=theory, practical=practical)


for idx, item in enumerate(test):
    if idx % 50 == 0:
        print("Cleaning Record Number {}".format(idx))
    html = item.html
    parse_and_store_result(html)
