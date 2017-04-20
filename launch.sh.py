from collections import namedtuple
from optparse import OptionParser

from downloader import output_ranges

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


def return_pairs(lower_bound, upper_bound, chunk_size=10000):
    lowers = list(range(0, upper_bound - lower_bound, chunk_size))
    uppers = [num + chunk_size for num in lowers[:-1]] + [lowers[-1] + (upper_bound % chunk_size)]
    return list(zip(lowers, uppers))


ranges = [Range(l, p, t, *output_ranges(l, p, t)[:2]) for l in level for p in part for t in type_]

pairs = [PairedRange(pair.level, pair.part, pair.type, return_pairs(pair.lowerbound, pair.upperbound),
                     len(return_pairs(pair.lowerbound, pair.upperbound))) for pair in ranges]

command_string = "docker run --detach -v /d/experiments/fbise/data:/app/fbise/data -v /d/experiments/fbise/logs:/app/logs --name worker{:0>2} localhost:5000/fbise /app/fbise/downloader.py -s {} -e {} -l {} -p {} -t {}"

template = """
#! /bin/bash

{}
"""

for pair in pairs:
    with open("launch-{}-{}-{}.sh".format(pair.level, pair.part, pair.type), 'w') as f:
        commands = []
        for n in range(pair.numbounds):
            commands.append(
                command_string.format(n, pair.bounds[n][0], pair.bounds[n][1], pair.level, pair.part, pair.type))
        f.write(template.format('\n'.join(commands)))
