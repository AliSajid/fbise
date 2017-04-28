import os
import sqlite3
from collections import namedtuple
from optparse import OptionParser

from requests import post

# Setting up the option parser
parser = OptionParser()

parser.add_option("-l", "--level", dest="level", type="str")
parser.add_option("-p", "--part", dest="part", type="str")
parser.add_option("-t", "--type", dest="type", type="str")

(options, args) = parser.parse_args()

DBDIR = "data"
DBNAME = "{}-{}-{}-complete.sqlite".format(options.level, options.part, options.type)

conn = sqlite3.connect(os.path.join(DBDIR, DBNAME))
cursor = conn.cursor()

cursor.execute("""SELECT idx FROM Record WHERE error = 1""")
errors = [item[0] for item in cursor.fetchall()]


def visit(url, rollno, error_idx):
    """
    This method visits the given site, fills the form, checks if a valid result is generated, adds the valid result 
    and the valid roll number to the valid dict and valid list respectively.

    :param error_idx: 
    :param url: 
    :param rollno: 
    """
    try:
        # noinspection PyProtectedMember
        res = post(url, rollno._asdict())
        if res.status_code != 200:
            cursor.execute("UPDATE Record SET html = ?, error = 0 WHERE idx = ?", (res.text, error_idx))
    except Exception as e:
        pass


def output_ranges(level, part, type):
    if type == "A":
        if level == "SSC":
            if part == "I":
                return 900001, 998600, "http://www.fbise.edu.pk/res-ssc-I.php"
            if part == "II":
                return 100001, 199000, "http://www.fbise.edu.pk/res-ssc-II.php"
        elif level == "HSSC":
            if part == "I":
                return 300001, 395100, "http://www.fbise.edu.pk/res-hssc-I.php"
            if part == "II":
                return 500001, 595100, "http://www.fbise.edu.pk/res-hssc-II.php"
        else:
            print("Invalid Level, Part or Type. Please check and try again.")
    elif type == "S":
        if level == "SSC":
            return 200001, 282000, "http://www.fbise.edu.pk/res-sscsup.php"
        if level == "HSSC":
            return 600001, 695100, "http://www.fbise.edu.pk/res-hsscsup.php"
    else:
        print("Invalid Level, Part or Type. Please check and try again.")


# Named tuple for RollNo
RollNo = namedtuple("RollNo", ['roll_no', "idx", "search"])


def download_data(level, part, type):
    from_num, to_num, url = output_ranges(level, part, type)

    print("Generating the list of Roll Numbers")
    nums = list(range(from_num, to_num + 1))

    print("Total records with errors: {}".format(len(errors)))

    rnlist = [RollNo(str(n), idx, "") for idx, n in enumerate(nums)]

    for idx, error in enumerate(errors):
        if idx % 25 == 0:
            conn.commit()
        print("Getting data for RollNo: {}".format(rnlist[error].roll_no))
        visit(url, rnlist[error], error)


conn.commit()

if __name__ == '__main__':
    download_data(options.level, options.part, options.type)
