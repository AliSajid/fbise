"""
This file contains the basic code to download and store all the data for the 5th and 8th class exam from the Punjab Education Commission
Website. This site achieves that by doing the following:

1. It runs through the entire list of possible roll numbers from '00-000-000' to '99-999-999'.
2. After every page load, it checks if a result was returned. If it was, it stores that result into a local sqplite db indexed
by the roll number, otherwise it commits a NULL to it.
3. After the run is complete, it takes the db and processes the data.
"""
import logging
import random
import sys
import time
from collections import namedtuple
from optparse import OptionParser
from os import path

from fake_useragent import UserAgent
from pony import orm
from requests import post

from models import db, Record

# Random wait time
DISTRIBUTION = list(range(50, 101, 10))
WAIT = random.choice(DISTRIBUTION)

# User Agent Spoofing
UA = UserAgent()

# Setting up the option parser
parser = OptionParser()

parser.add_option("-s", "--start-num", dest="start", type="int")
parser.add_option("-e", "--end-num", dest="end", type="int")
parser.add_option("-l", "--level", dest="level", type="str")
parser.add_option("-p", "--part", dest="part", type="str")
parser.add_option("-t", "--type", dest="type", type="str")

(options, args) = parser.parse_args()

# Setting up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d-%Y %H:%M:%S,',
                    filename=path.join("logs",
                                       "{}-{}-{}-data-{:0>6}-{:0>6}-{}.log".format(options.level, options.part,
                                                                                   options.type, options.start,
                                                                                   options.end, 2018)),
                    filemode='a'
                    )
logger = logging.getLogger(__name__)

# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)

# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')

# tell the handler to use this format
console.setFormatter(formatter)

# add the handler to the root logger
logger.addHandler(console)

# Named tuple for RollNo
RollNo = namedtuple("RollNo", ['roll_no', "idx", "search"])

# Database Setup
DBNAME = "{}-{}-{}-data-{:0>6}-{:0>6}-{year}.sqlite".format(options.level, options.part, options.type, options.start,
                                                            options.end, year=2018)
DIRNAME = "data"

db.bind('sqlite', path.join(DIRNAME, DBNAME), create_db=True)

db.generate_mapping(create_tables=True)


def output_ranges(level, part, type):
    if type == "A":
        if level == "SSC":
            if part == "I":
                return 900001, 999999, "https://www.fbise.edu.pk/res-ssc-I.php"
            if part == "II":
                return 100001, 199999, "https://www.fbise.edu.pk/res-ssc-II.php"
        elif level == "HSSC":
            if part == "I":
                return 300001, 399999, "https://www.fbise.edu.pk/res-hssc-I.php"
            if part == "II":
                return 500001, 599999, "https://www.fbise.edu.pk/res-hssc-II.php"
        else:
            logger.critical("Invalid Level, Part or Type. Please check and try again.")
    elif type == "S":
        if level == "SSC":
            return 200001, 299999, "https://www.fbise.edu.pk/res-sscsup.php"
        if level == "HSSC":
            return 600001, 699999, "https://www.fbise.edu.pk/res-hsscsup.php"
    else:
        logger.critical("Invalid Level, Part or Type. Please check and try again.")


@orm.db_session
def visit(url, rollno, idx):
    """
    This method visits the given site, fills the form, checks if a valid result is generated, adds the valid result 
    and the valid roll number to the valid dict and valid list respectively.

    :param idx:
    :param url: 
    :param rollno: 
    """
    try:
        # noinspection PyProtectedMember

        header = {'User-Agent': str(UA.random),
                  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                  "Accept-Encoding": "gzip, deflate, br",
                  "Accept-Language": "en-US,en;q=0.9",
                  "Connection": "keep-alive",
                  "Content-Type": "application/x-www-form-urlencoded",
                  "Host": "www.fbise.edu.pk",
                  "Origin": "https://www.fbise.edu.pk",
                  "Referer": "https://www.fbise.edu.pk/res-hssc-II.php",
                  "Upgrade-Insecure-Requests": "1",
                  }
        res = post(url, rollno._asdict(), headers=header)
        if res.status_code != 200:
            Record(rollno=rollno[0], html="NULL", error=True, idx=idx)
        else:
            Record(rollno=rollno[0], html=res.text, error=False, idx=idx)
    except Exception as e:
        logger.error(str(e))
        Record(rollno=rollno[0], html="NULL", error=True, idx=idx)


# noinspection PyTypeChecker, PyTypeChecker
def download_data(start_num, end_num, level, part, type):
    from_num, to_num, url = output_ranges(level, part, type)

    logger.info("Generating the list of Roll Numbers")
    nums = list(range(from_num, to_num + 1))

    rnlist = [RollNo(str(n), idx, "") for idx, n in enumerate(nums)]

    logger.info("Start Parameter is: {}".format(start_num))
    logger.info("End Parameter is: {}".format(end_num))
    logger.info("Saving data to database {}".format(DBNAME))

    try:
        with orm.db_session:
            # noinspection PyTypeChecker
            last_record = orm.max(r.id for r in Record)

            if last_record == end_num:
                logger.info("No new data to download. Exiting...")
                return

            if last_record:
                # noinspection PyTypeChecker
                last_idx = orm.select(r.idx for r in Record if r.id == last_record)[:][0]
                start = last_idx + 1
            else:
                start = start_num

        logger.info("Starting the Brute Force Search from position {}".format(start))
        logger.info("Process started at {}".format(time.strftime('%c')))

        for idx, rn in enumerate(rnlist[start:end_num]):
            if idx % WAIT == 0:
                time.sleep(5)
            if idx % 25 == 0:
                logger.info("Downloading data for Roll No. {}".format(rn.roll_no))
            visit(url, rn, idx=rn.idx)
        logger.info("Process ended at {}".format(time.strftime('%c')))
    except KeyboardInterrupt as err:
        logger.exception("{0}".format(err))
        logger.exception("Recieved Keyboard Interrupt. Exiting.")
    except:
        logger.exception("Unexpected error:", sys.exc_info()[0])
        raise


if __name__ == '__main__':
    download_data(options.start, options.end, options.level, options.part, options.type)
