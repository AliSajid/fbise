from collections import namedtuple
from optparse import OptionParser

# Setting up the option parser
parser = OptionParser()

parser.add_option("-l", "--level", dest="level", type="str")
parser.add_option("-p", "--part", dest="part", type="str")
parser.add_option("-t", "--type", dest="type", type="str")
parser.add_option("-c", "--chunk", dest="chunk", type="int", default=10000)

(options, args) = parser.parse_args()

Range = namedtuple("Range", ["level", "part", "type", "lowerbound", "upperbound"])
PairedRange = namedtuple("PairedRange", ["level", "part", "type", "bounds", "numbounds"])

if options.level:
    level = [options.level]
else:
    level = ["SSC", "HSSC"]
if options.part:
    part = [options.part]
else:
    part = ["I", "II"]
if options.type:
    type_ = [options.type]
else:
    type_ = ["A", "S"]


def output_ranges(level, part, type):
    if type == "A":
        if level == "SSC":
            if part == "I":
                return 900001, 999999, "http://www.fbise.edu.pk/res-ssc-I.php"
            if part == "II":
                return 100001, 199999, "http://www.fbise.edu.pk/res-ssc-II.php"
        elif level == "HSSC":
            if part == "I":
                return 300001, 399999, "http://www.fbise.edu.pk/res-hssc-I.php"
            if part == "II":
                return 500001, 599999, "http://www.fbise.edu.pk/res-hssc-II.php"
        else:
            print("Invalid Level, Part or Type. Please check and try again.")
    elif type == "S":
        if level == "SSC":
            return 200001, 299999, "http://www.fbise.edu.pk/res-sscsup.php"
        if level == "HSSC":
            return 600001, 699999, "http://www.fbise.edu.pk/res-hsscsup.php"
    else:
        print("Invalid Level, Part or Type. Please check and try again.")


def return_pairs(lower_bound, upper_bound, chunk_size):
    lowers = list(range(0, upper_bound - lower_bound, chunk_size))
    uppers = [num + chunk_size for num in lowers[:-1]] + [lowers[-1] + (upper_bound % chunk_size)]
    return list(zip(lowers, uppers))


ranges = [Range(l, p, t, *output_ranges(l, p, t)[:2]) for l in level for p in part for t in type_]

pairs = [PairedRange(pair.level, pair.part, pair.type,
                     return_pairs(pair.lowerbound, pair.upperbound, chunk_size=options.chunk),
                     len(return_pairs(pair.lowerbound, pair.upperbound, chunk_size=options.chunk))) for pair in ranges]

command_string = "docker run --detach -v /d/experiments/fbise/data:/app/fbise/data -v /d/experiments/fbise/logs:/app/logs --name worker{:0>2} localhost:5000/fbise /opt/conda/bin/python /app/fbise/downloader.py -s {} -e {} -l {} -p {} -t {}"

template = """#! /bin/bash

{}
"""

for index, pair in enumerate(pairs):
    with open("launch-{}-{}-{}.sh".format(pair.level, pair.part, pair.type), 'w') as f:
        commands = []
        for n in range(pair.numbounds):
            commands.append(
                command_string.format(str(index) + str(n), pair.bounds[n][0], pair.bounds[n][1], pair.level, pair.part, pair.type))
        f.write(template.format('\n\n'.join(commands)))
