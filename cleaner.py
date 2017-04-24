import os
from collections import defaultdict
from optparse import OptionParser

from bs4 import BeautifulSoup
from pony import orm

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

dbout = orm.Database()
dbout.bind('sqlite', os.path.join(DBDIR, OUTPUTDBNAME), create_db=True)
dbout.generate_mapping(create_tables=True)

with orm.db_session:
    test = orm.select(c for c in Record).limit(10)


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


@orm.db_session
def parse_and_store_result(html):
    soup = BeautifulSoup(html, 'lxml')
    info, result = split_tables(soup)
    parsed_info = parse_info(info)
    parsed_result = parse_results(result)
