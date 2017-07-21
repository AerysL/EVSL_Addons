"""
Parses the output and stats file from EVSL. Currently tested on MMPLanN, but
should work for for all matrix market reading libraries.
Example call:

    ./MMPlanN.ex > stats.txt
    python /path/to/parser.py -i OUT/MMPlanN_stiff1 -s stats.txt

    Or, using the automatic detection of files

    python /path/to/parser.py -d .

    Which as -d defaults to . , can be shortened to
    python /path/to/parser.py

    Should you have a layout similar to
    Ge87H76
        OUT/MMPLanN_*
        stats*
    Ge87H76
        OUT/MMPLanN_*
        stats*

Should be able to to detect if you are using one or many slices and give
appropriate output.
"""
import re
import mmap
import argparse
import os
STATS = {
    r"Iterative solver": [r"([0-9.]+)", ["sec_total"]],
    r"Pol\(A\)\*v": [r"([0-9.]+)\s\(\s*([0-9]+), avg ([0-9.]+)\)",
                     ["sec_pol", "num_pol", "avg_pol"]],
    r"Matvec matrix A": [r"([0-9.]+)\s\(\s*([0-9]+), avg ([0-9.]+)\)",
                         ["sec_matvec", "num_matvec", "avg_matvec"]],

    r"Reorthogonalization": [r"([0-9.]+)", ["sec_orth"]],
    r"LAPACK eig": [r"([0-9.]+)", ["sec_lapack"]],
    r"Compute Ritz vectors": [r"([0-9.]+)", ["sec_ritz"]],
    r"Some other thing timed": [r"([0-9.]+)", ["sec_other"]],
    r"Setup Solver for A-SIG\*B": [r"([0-9.]+)", ["sec_setup_solve"]],
    r"Rat\(A\)\*v": [r"([0-9.]+)\s\(\s*([0-9]+), avg ([0-9.]+)\)",
                     ["sec_fact", "num_fact", "avg_fact"]],
    r"Solve with A-SIGMA\*B": [r"([0-9.]+)\s\(\s*([0-9]+), avg ([0-9.]+)\)",
                               ["sec_solve", "num_solve", "avg_solve"]],
    r"Compute Ritz vectotrs": [r"([0-9.]+)", ["sec_ritz"]]
}
TIMING_REGEX = r'\s+Timing \(sec\):'
DEG_REGEX = r'\s+polynomial deg ([0-9]+)'
NAME_REGEX = r'MATRIX: ([!-~]+)...'
ITERATION_REGEX = r'k\s+([0-9]+): nconv\s+[0-9]+\s+tr1\s+'
EV_START_REGEX = r'\s+Computed \[([0-9]+) out of ([0-9]+) estimated\]\s+'
SUBINTERVAL_REGEX = r'\s+subinterval: \[\s+(\-?[0-9.]+e.\-?[0-9]+) ,\s+(\-?[0-9.]+e.\-?[0-9]+)'
EV_REGEX = r'\s+(\-?[0-9.]+e.[0-9]+)\s+(\-?[0-9.]+e.[0-9]+)'
SLICE_START_REGEX = r'Steb 1b: Slices found:'
SLICE_REGEX = r'\[\s+([\-0-9.]+e.[\-0-9]) ,\s+([\-0-9.]+e.[\-0-9]+)\]'
PARTITION_RERGEX = r'Partition the interval of interest \[([\-0-9.]+),([\-0-9.]+)\] into ([0-9]+) slice'


MM_P_STATS_SOLO = ['num_deg', 'num_iter', 'num_matvec',
            'sec_matvec', 'sec_orth', 'sec_total',
            'max_res']
MM_R_STATS_SOLO = ['num_iter', 'num_matvec', 'num_solve',
              'sec_fact', 'sec_solve', 'sec_orth', 'sec_total',
            'max_res']

MM_P_STATS_SLICE = ['num_ev', 'num_deg', 'num_iter', 'num_matvec',
            'sec_matvec', 'sec_orth', 'sec_total',
            'max_res']
MM_R_STATS_SLICE = ['num_ev', 'num_iter', 'num_matvec', 'num_solve',
              'sec_fact', 'sec_solve', 'sec_orth', 'sec_total',
            'max_res']
MM_HEADER = ['deg', 'iter', 'matvec', ['CPU time (sec)', ['matvec', 'orth',
                                                          'total']], 'max\
             residual']
STATS_PREFIX = ['run-time', 'stats']
OUT_PREFIX = ['MMPLanN', 'MMPLanR', 'MMRLanN', 'MMRLanR']

def parse_matrix_output(stats_file_name, out_file_name, obj):
    with open(stats_file_name) as f:
        parse_stats(f, obj)
    with open(out_file_name) as f:
        parse_out(f, obj)
    return obj

def type_cast(key, val):
    if(key[:3] == "num"):
        return int(val)
    elif(key[:3] == "sec"):
        return float(val)
    elif(key[:3] == "avg"):
        return float(val)
    else:
        print("Unknown typecast")
        print(key[:3])
        exit(-1)

def handle_regex_stuff(line):
    for (key, value) in STATS.items():
        fullreg = r"\s*%s\s+:\s*%s" % (key, value[0])
        match = re.match(fullreg, line)
        if match:
            for (name, group) in zip(value[1], match.groups()):
                return ('stat', zip(value[1], match.groups()))

    time_match = re.match(TIMING_REGEX, line)
    if(time_match):
        return ('timing', None)


def find_partition_info(data_left):
    match = re.match(PARTITION_RERGEX, data_left)
    return match


def find_slice_start(data_left):
    match = re.match(SLICE_START_REGEX, data_left)
    return match


def find_slice(data_left):
    match = re.match(SLICE_REGEX, data_left)
    return match


def find_deg(data_left):
    match = re.match(DEG_REGEX, data_left)
    return match


def find_subinterval(data_left):
    match = re.match(SUBINTERVAL_REGEX, data_left)
    return match

def find_name(data_left):
    match = re.match(NAME_REGEX, data_left)
    return match


def find_int_check(data_left):
    match = re.match(ITERATION_REGEX, data_left)
    return match


def find_ev_start(data_left):
    match = re.match(EV_START_REGEX, data_left)
    return match


def find_ev_check(data_left):
    match = re.match(EV_REGEX, data_left)
    return match


def res_to_latex(res):
    res_reg = r"([0-9.]+)e(.[0-9]+)"
    match = re.match(res_reg, str(res))
    return "$%s\\!\\times\\!10^{%s}$" % (match.groups()[0], match.groups()[1])


def get_deg(data, obj):
    for line in data:
        deg_info = find_deg(line)
        if deg_info:
            obj.attrs['num_deg'] = float(deg_info.groups()[0])
            break


def get_iterations(data, obj):
    for line in data:
        int_check = find_int_check(line)
        if int_check:
            break

    old_match = None
    for line in data:
        int_check = find_int_check(line)
        if not int_check:
            obj.attrs['num_iter'] = int(old_match.groups()[0])
            break
        old_match = int_check

def get_slice_info(data, obj):
    for line in data:
        int_check = find_int_check(line)
        if int_check:
            break


def get_res(data, obj):
    for line in data:
        ev_check = find_ev_start(line)
        if ev_check:
            obj.attrs['num_ev'] = ev_check.groups()[0]
            break
    res = 0
    for line in data:
        ev_check = find_ev_check(line)
        if ev_check:
            res = max(float(ev_check.groups()[1]), res)
        else:
            break
    obj.attrs['max_res'] = float(res)  # res_to_latex(res)


def get_subinterval(data, obj):
    for line in data:
        subinterval_info = find_subinterval(line)
        if subinterval_info:
            obj.interval_left = float(subinterval_info.groups()[0])
            obj.interval_right = float(subinterval_info.groups()[1])
            break

def get_mat_name(data, obj):
    for line in data:
        name_info = find_name(line)
        if name_info:
            obj.set_name(name_info.groups()[0])
            break


def get_partition_info(data, obj):
    for line in data:
        partition_info = find_partition_info(line)
        if partition_info:
            obj.interval_left = float((partition_info.groups()[0]))
            obj.interval_right = float((partition_info.groups()[1]))
            obj.num_slices = int((partition_info.groups()[2]))
            break

def parse_out(data, obj):
    get_mat_name(data, obj)
    get_partition_info(data, obj)
    for i in range(obj.num_slices):
        new_slice = obj.slices[i]
        get_subinterval(data, new_slice)
        if obj.filter_type == "P":
            get_deg(data, new_slice)
        get_iterations(data, new_slice)
        get_res(data, new_slice)
    return obj
    # Go until start of interation checks


def parse_stats(data, obj):
    cur_slice = None
    for line in data:
        res = handle_regex_stuff(line)
        if res:
            (match_type, pairs) = res
            if match_type == "stat":
                for pair in pairs:
                    cur_slice.attrs[pair[0]] = type_cast(pair[0], pair[1])
            elif match_type == "timing":
                if cur_slice:
                    obj.add_slice(cur_slice)
                cur_slice = Slice(obj)

    obj.add_slice(cur_slice)
    obj.num_slices = len(obj.slices)

    if 'sec_solve' in obj.attrs:
        obj.filter_type = 'R'
    else:
        obj.filter_type = 'P'

class Slice(object):
    def __init__(self, parent):
        self.attrs = {}
        self.parent = parent
        self.interval_left = 0
        self.interval_right = 0

    def __str__(self):
        ret = ""
        for (key, value) in self.attrs.items():
            ret += "%s: %s\n" % (key, value)
        return ret

    def to_latex(self):
        ret = ""
        if self.parent.mat_type == "MM" and self.parent.filter_type == "P":
            ret += "[%s, %s]"% (self.interval_left, self.interval_right)
            for pair in MM_P_STATS_SLICE:
                ret += "& $%s$" % self.attrs[pair]
        if self.parent.mat_type == "MM" and self.parent.filter_type == "R":
            ret += self.name_to_latex()
            for pair in MM_R_STATS_SLICE:
                ret += "& $%s$" % self.attrs[pair]
        ret += "\\\\"
        return ret



class Result_list(object):
    def __init__(self, res={}, mat_type="MM"):
        self.res = res
        self.mat_type = mat_type
    def add_result(self,result):
        self.res[result.mat_name] = result

    def to_latex(self):
        ret = ""
        if self.mat_type == "MM":
            for item in self.res.values():
                ret += '%s\n' % item.to_latex()
        ret += "\\\\"
        return ret



class Result(object):
    def __init__(self, mat_type="MM", filter_type="P", attrs={}):
        self.attrs = attrs
        self.mat_type = mat_type
        self.filter_type = filter_type
        self.mat_name = None
        self.slices = []
        self.num_slices = 0

    def set_name(self, name):
        self.mat_name = name

    def get_name(self):
        return self.mat_name

    def __str__(self):
        ret = ""
        for (key, value) in self.attrs.items():
            ret += "%s: %s\n" % (key, value)
        for slc in self.slices:
            ret += str(slc)
        return ret

    def add_slice(self, new_slice):
        self.slices.append(new_slice)

    def name_to_latex(self):
        ret = ""
        ret += """$\mathrm{"""
        if self.get_name():
            name = self.get_name()
        else:
            print('Mat_name doesnt exist')
            return ""
            exit(-1)
        while name != "":
            end = 0
            letter = r"^[A-Za-z]+"
            number = r"^[0-9]+"
            letter_match = re.match(letter, name)
            number_match = re.match(number, name)
            if letter_match:
                ret += letter_match.group(0)
                end = letter_match.span()[1]
                name = name[end:]
            elif number_match:
                ret += "_{"
                ret += number_match.group(0)
                ret += "}"
                end = number_match.span()[1]
                name = name[end:]
            else:
                print('Unsure how to parse name')
                exit(-1)
        ret += "}$"
        return ret

    def to_latex(self):
        ret = ""
        if(len(self.slices) > 1):
            for slc in self.slices:
                ret += slc.to_latex()
                ret += "\n"
        elif(len(self.slices) == 1):
            if self.mat_type == "MM" and self.filter_type == "P":
                ret += self.name_to_latex()
                for pair in MM_P_STATS_SOLO:
                    if pair in self.attrs:
                        if pair == "max_res":
                            ret += "& %s" % res_to_latex(self.attrs[pair])
                        else:
                            ret += "& $%s$" % self.attrs[pair]
                    else:
                        if pair == "max_res":
                            ret += "& %s" % res_to_latex(self.slices[0].attrs[pair])
                        else:
                            ret += "& $%s$" % self.slices[0].attrs[pair]
            if self.mat_type == "MM" and self.filter_type == "R":
                ret += self.name_to_latex()
                for pair in MM_R_STATS_SOLO.items():
                    if pair in self.attrs:
                        if pair == "max_res":
                            ret += "& %s" % res_to_latex(self.attrs[pair])
                        else:
                            ret += "& $%s$" % self.attrs[pair]
                    else:
                        if pair == "max_res":
                            ret += "& %s" % res_to_latex(self.slices[0].attrs[pair])
                        else:
                            ret += "& $%s$" % self.slices[0].attrs[pair]
        elif(len(slices) == 0):
            print('No slices to output')
            exit(-1)
        ret += "\\\\"
        return ret

def find_stats_file(directory):
    files = os.listdir(directory)
    candidates = list(filter(lambda x: x.startswith(tuple(STATS_PREFIX)), files))
    if(len(candidates) > 1):
        print('Many candidates for stat file found: %s' % candidates)
        exit(-1)
    elif(len(candidates) == 1):
        print('Using only candidatefor stat file: %s' % candidates[0])
        return '%s/%s' % (directory,candidates[0])
    elif(len(candidates) == 0):
        print('No stat file candidate found, please supply one with -s')
        exit(-1)

def find_out_file(directory):
    files = os.listdir('%s/OUT' % directory)
    candidates = list(filter(lambda x: x.startswith(tuple(OUT_PREFIX)), files))
    if(len(candidates) > 1):
        print('Many candidates for stat file found: %s' % candidates)
        exit(-1)
    elif(len(candidates) == 1):
        print('Using only candidatefor stat file: %s' % candidates[0])
        return '%s/OUT/%s' % (directory,candidates[0])
    elif(len(candidates) == 0):
        print('No stat file candidate found, please supply one with -s')
        exit(-1)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--stats', 
        help="""The stats file, which is referred to as fstats internally. 
        Looks like:
          Timing (sec):
        Iterative solver   : ...""")
    parser.add_argument(
        '-i', '--input', 
        help="""The outputfile, should be found in OUT/*. Starts with:
        MATRIX:...
        Partition the interval of interest ...
    """)
    parser.add_argument(
        '-d', '--dir', default=".",
        help="""Directory to look for the stats and OUT file""")
    parser.add_argument(
        '-l', '--list',  nargs='+',
        help="""Directory to look for the stats and OUT file""")
    args = parser.parse_args()
        
    if args.list is not None:
        for directory in args.list:
            test_obj = Result()
            stats = find_stats_file(directory)
            inp = find_out_file(directory)
            parse_matrix_output(stats, inp, test_obj)
            print(test_obj.to_latex())
        print('Finished parsing list')
        exit(0)


    if args.stats is None:
        args.stats = find_stats_file(args.dir)
        if not args.stats:
            print('No stats file found')
            exit(-1)

    if args.input is None:
        args.input = find_out_file(args.dir)
        if not args.input:
            print('No OUT file found')
            exit(-1)

    test_obj = Result()
    parse_matrix_output(args.stats, args.input, test_obj)
    print(test_obj)
    for slc in test_obj.slices:
        print(slc.to_latex())
    print(test_obj.to_latex())
