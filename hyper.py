"""
Used to generate many permutations of options for EVSL, prepared for a PBS job.

Currently uses the parameters coded below, not command line. 

Example call:
	python hyper.py

"""
import itertools
import multiprocessing
import subprocess
import os
import errno
import time
NUM_ALLOC_RAM = ["10gb"]
NUM_ALLOC_HOURS = [0]
NUM_ALLOC_MINUTES = [7]
NUM_ALLOC_SECONDS = [0]
# NUM_ALLOC_CORES = [4]
NUM_USED_THREADS = [22]
# MKL_USED_THREADS = [1, 2, 4]
MKL_DYNAMIC = ["false"]
OMP_DYNAMIC = ["false"]
MAT_TYPE = ["MM"]
METHOD_RESTART = ["N"]
METHOD_FILTER = ["P"] # , "R"]
METHOD_LANCZOS = ["Lan"]
MAT_NAME = ["Ge87H76" ,"Ge99H100", "Si41Ge41H72", "Si87H76", "Ga41As41H72"]
#MAT_NAME = ["LAP"]
NUM_ALLOC_MINUTES_LONG = [20]
NUM_ALLOC_HOURS_LONG = [0]
NUM_ALLOC_SECONDS_LONG = [0]
MAT_LONG = ["Ga41As41H72"]

EIG_PROB = ["STD"]

MAT_NZ = [49]
MAT_NY = [49]
MAT_NX = [49]
A_BOUND = [1.0]
B_BOUND = [1.1]

NUM_SLICES = [1]

EMAIL_OPT = ["abe"]
EMAIL_ADDR = ["erlan086@umn.edu"]

EVSL_DIR = "/home/luke/dev/EVSL"
BASE_GEN_DIR = "/home/luke/tests"

#CONFIG ENDS HERE
VARS = [ NUM_ALLOC_RAM,   NUM_USED_THREADS, MKL_DYNAMIC, OMP_DYNAMIC, MAT_TYPE, METHOD_RESTART, METHOD_FILTER, METHOD_LANCZOS, MAT_NAME, EIG_PROB, MAT_NZ, MAT_NY, MAT_NX, NUM_SLICES, EMAIL_OPT, EMAIL_ADDR, A_BOUND, B_BOUND]
NAMES =["NAR",  "NUT",  "MD", "OD", "MT", "MR", "MF", "ML", "MN", "EIG_PROB", "NZ", "NY", "NX", "NS", "EMAIL_OPT", "EMAIL_ADDR", "A_BOUND", "B_BOUND"]

ZIPPED = list(zip(NAMES, VARS))
CONTROLS = [(x_y2[0], x_y2[1][0]) for x_y2 in [x_y for x_y in ZIPPED if len(x_y[1]) == 1]]
CONTROL_SUBDIR = "_".join("%s=%s" % tup for tup in CONTROLS)
GEN_DIR = BASE_GEN_DIR + "/" +  CONTROL_SUBDIR + str(int(time.time()))


def generate_wrapper_s(IN_VARS):
	(NAR,  NUT,  MD, OD, MT, MR, MF, ML, MN, EIG_PROB, NZ, NY, NX, NS,EMAIL_OPT, EMAIL_ADDR, A_BOUND, B_BOUND) = IN_VARS
	print('here')
	TEST = list(zip(NAMES, IN_VARS))
	COM = "%s/generate-test.sh" % os.path.dirname(os.path.realpath(__file__))
	ARGS = list("--%s=%s" % (x,y) for (x,y) in TEST)
	ARGS.insert(0,COM)
	MY_ZIPPED = list(zip(NAMES, VARS, IN_VARS))
	print('there')
	PARAMS = [(x_y_z1[0], x_y_z1[2]) for x_y_z1 in [x_y_z for x_y_z in MY_ZIPPED if len(x_y_z[1]) > 1]]
	print('kere')
	NAME = "_".join("%s=%s" % tup for tup in PARAMS)
	print(NAME)
	ARGS.append("--NAME=%s" %NAME)
	ARGS.append("--GEN_DIR=%s" %GEN_DIR)
	ARGS.append("--EVSL_DIR=%s" %EVSL_DIR)
	ARGS.append("--NAC=24")
	if(MN in MAT_LONG):
		ARGS.append("--NAH=%s" %NUM_ALLOC_HOURS_LONG[0])
		ARGS.append("--NAM=%s" %NUM_ALLOC_MINUTES_LONG[0])
		ARGS.append("--NAS=%s" %NUM_ALLOC_SECONDS_LONG[0])
	else:
		ARGS.append("--NAH=%s" %NUM_ALLOC_HOURS[0])
		ARGS.append("--NAM=%s" %NUM_ALLOC_MINUTES[0])
		ARGS.append("--NAS=%s" %NUM_ALLOC_SECONDS[0])
	print(ARGS)
	subprocess.call(ARGS)
	
if __name__ == "__main__":
	print(GEN_DIR)
	ZIPPED = list(zip(NAMES, VARS))
	try:
	    os.makedirs(GEN_DIR)
	except OSError as e:
	    if e.errno != errno.EEXIST:
	        raise
	print('mere')
	pool = multiprocessing.Pool(processes=1)
	#Don't run this multiprocessor, the generating script can't handle it
	result = pool.map(generate_wrapper_s,itertools.product(*VARS))
	target = open("commands", 'w')
	target.write("A command that may be useful(after module load parallel): ls */*.pbs | parallel \"qsub -q mesabi {}\"");
	target.close()
