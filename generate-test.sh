#!/bin/sh
#Generates a PBS file for a given configuration
#Currently only tested for Lap{R/P}LanN
#REQUIRES GNU getopt
#NUM_ALLOC_CORES=1 #NAC
NUM_ALLOC_RAM="60gb" #NAR, user specified units
NUM_ALLOC_HOURS=0 #NAH
NUM_ALLOC_MINUTES=15 #NAM
NUM_ALLOC_SECONDS=0 #NAS
NUM_USED_THREADS=1 #NUT
#MKL_USED_THREADS=1 #MUT
MKL_DYNAMIC="FALSE" #MD
OMP_DYNAMIC="FALSE" #OD
MAT_TYPE="Lap" # or Lap #MT
METHOD_RESTART="N" #or R #MR
METHOD_FILTER="P" #or R #MF
METHOD_LANCZOS="Lan" #or P #ML

EIG_PROB="STD" # STD:Standard Eigenvalue problem, GEN: General Eigenvalue problem
#if MAT_TYPE="MM"
MAT_NAME="Ge87H76" #MN
#else
MAT_NZ=10 #NZ
MAT_NY=10 #NY
MAT_NX=10 #NX
NUM_SLICES=1 #NS
A_BOUND=0 #NS
B_BOUND=1 #NS
#endif

EVSL_DIR="/home/saady/shared/EVSL" #NO SLASH #Where there EVSL Library is
GEN_DIR="/home/saady/erlan086/tests" #NO SLASH #Where to output the test

EMAIL_ADDR="erlan086@umn.edu" #Your Email
EMAL_OPT="abe" # On abort, begin, and error
SERIAL_NUM=$(date +%s) #Defaults to current time
SERIAL_NUM_GEN='$(date +%s)' #Defaults to current time



##Should not be any need to change below here.

OPTS=`getopt -o v --long NAC:,NAR:,NAH:,NAM:,NAS:,NUT:,MUT:,MD:,OD:,MT:,MR:,MF:,ML:,MM:,MN:,NZ:,NY:,NX:,NS:,NAME:,EMAIL_OPT:,EMAIL_ADDR:,EVSL_DIR:,GEN_DIR:,EIG_PROB:,A_BOUND:,B_BOUND:,SNG:,SN: -n 'parse-options' -- "$@"`
if [ $? != 0 ]; then echo "Failed parsing options." >&2; exit 1 ; fi

eval set -- "$OPTS"
while true; do
    case "$1" in
      --NUM_ALLOC_CORES | --NAC ) NUM_ALLOC_CORES="$2"; shift; shift ;;
      --NUM_ALLOC_RAM | --NAR ) NUM_ALLOC_RAM="$2"; shift; shift ;;
      --NUM_ALLOC_HOURS | --NAH ) NUM_ALLOC_HOURS="$2"; shift; shift ;;
      --NUM_ALLOC_MINUTES | --NAM ) NUM_ALLOC_MINUTES="$2"; shift; shift ;;
      --NUM_ALLOC_SECONDS | --NAS ) NUM_ALLOC_SECONDS="$2"; shift; shift ;;
      --NUM_USED_THREADS | --NUT ) NUM_USED_THREADS="$2"; shift; shift ;;
      --MKL_USED_THREADS | --MUT ) MKL_USED_THREADS="$2"; shift; shift ;;
      --MKL_DYNAMIC | --MD ) MKL_DYNAMIC="$2"; shift; shift ;;
      --OMP_DYNAMIC | --OD ) OMP_DYNAMIC="$2"; shift; shift ;;
      --MAT_TYPE | --MT  ) MAT_TYPE="$2"; shift; shift ;;
      --METHOD_RESTART | --MR  ) METHOD_RESTART="$2"; shift; shift ;;
      --METHOD_FILCTER | --MF  ) METHOD_FILTER="$2"; shift; shift ;;
      --METHOD_LANCZOS | --ML  ) METHOD_LANCZOS="$2"; shift; shift ;;
      --MAT_NAME | --MN  ) MAT_NAME="$2"; shift; shift ;;
      --EIG_PROB  ) EIG_PROB="$2"; shift; shift ;;
      --SERIAL_NUM | --SN  ) MAT_NAME="$2"; shift; shift ;;
      --SERIAL_NUM_GEN | --SN_GEN  ) MAT_NAME="$2"; shift; shift ;;
      --NAME ) NAME="$2"; shift; shift;;
      --NS  ) NUM_SLICES="$2"; shift; shift ;;
      --NX  ) MAT_NX="$2"; shift; shift ;;
      --NY  ) MAT_NY="$2"; shift; shift ;;
      --NZ  ) MAT_NZ="$2"; shift; shift ;;
      --EMAIL_OPT  ) EMAIL_OPT="$2"; shift; shift ;;
      --EMAIL_ADDR  ) EMAIL_ADDR="$2"; shift; shift ;;
      --EVSL_DIR ) EVSL_DIR="$2"; shift; shift ;;
      --GEN_DIR ) GEN_DIR="$2"; shift; shift ;;
      --A_BOUND ) A_BOUND="$2"; shift; shift ;;
      --B_BOUND ) B_BOUND="$2"; shift; shift ;;
      -- ) shift; break ;;
      * ) break ;;
      esac
done


#IF number of cores to allocate is unspecified, allocate the max of num_used_threads and mkl_used_threads.
if [ -z ${MKL_USED_THREADS} ]; then MKL_USED_THREADS=$NUM_USED_THREADS; fi
if [ -z ${NUM_ALLOC_CORES} ]; then NUM_ALLOC_CORES=$(( NUM_USED_THREADS > MKL_USED_THREADS? NUM_USED_THREADS : MKL_USED_THREADS)); fi

ALTNAME="$METHOD_FILTER$METHOD_LANCZOS$METHOD_RESTART-$MAT_TYPE-$NUM_ALLOC_CORES-$NUM_USED_THREADS-"
if [ $MAT_TYPE == "MM" ] 
then
	ALTNAME="$NAME$MAT_NAME"
else
	ALTNAME="$ALTNAME-$MAT_NX-$MAT_NY-$MAT_NZ-$NUM_SLICES-$A_BOUND-$B_BOUND"
fi
if [ -z ${NAME} ]; then NAME=$ALTNAME; echo "Name is now $NAME";else echo "NAme is $NAME"; fi
if [ $EIG_PROB == "STD" ]
then
TESTFOLDER="$METHOD_FILTER$METHOD_LANCZOS$METHOD_RESTART"
TESTNAME="$MAT_TYPE$METHOD_FILTER$METHOD_LANCZOS$METHOD_RESTART"
echo "std"
else
TESTNAME="${MAT_TYPE}_${METHOD_FILTER}$METHOD_LANCZOS$METHOD_RESTART"
TESTFOLDER="GEN"
echo "gen"
fi

FOLDER="$GEN_DIR/$NAME-$SERIAL_NUM"
REL_FOLDER="$NAME"
if [ -d "$FOLDER" ] 
then
    echo "$FOLDER ALREADY EXISTS!, moving to backup location"
    tar --remove-files -czvf "$FOLDER.$SERIAL_NUM.tar.gz" "$REL_FOLDER"
fi
    
mkdir "$FOLDER"
FILE="$FOLDER/$NAME.pbs"

touch "$FILE"

#Setup header of PBS
echo '#!/bin/bash -l' > $FILE
echo "#PBS -l walltime=$NUM_ALLOC_HOURS:$NUM_ALLOC_MINUTES:$NUM_ALLOC_SECONDS,nodes=1:ppn=$NUM_ALLOC_CORES,mem=$NUM_ALLOC_RAM" >> $FILE
echo "#PBS -m $EMAL_OPT" >> $FILE
echo "#PBS -M $EMAIL_ADDR" >> $FILE
echo "#PBS -o $FOLDER/stdout-$SERIAL_NUM" >> $FILE
echo "#PBS -e $FOLDER/stderr-$SERIAL_NUM" >> $FILE

#Setup setup in pbs
echo "cd \"$FOLDER\"" >> $FILE
echo 'module load intel/2017/update4' >> $FILE

#Check if md5sum is same at runtime as is now
md5sum "$EVSL_DIR/EVSL_1.0/TESTS/$TESTFOLDER/$TESTNAME.ex" > "$FOLDER/$TESTNAME.ex.md5"
echo "if md5sum -c $TESTNAME.ex.md5; then echo \"MD5Matched\" ; else echo \"WARNING, CURRENT EX IS NOT SAME AS WHEN GENERATED\"; fi;" >> $FILE

#symlink executable, copy over source for checking purposes
ln -s  "$EVSL_DIR/EVSL_1.0/TESTS/$TESTFOLDER/$TESTNAME.ex" "$FOLDER/$TESTNAME.ex"
cp "$EVSL_DIR/EVSL_1.0/TESTS/$TESTFOLDER/$TESTNAME.c" "$FOLDER/"

#Setup command line call for PBS
COMMAND_LINE="OMP_NUM_THREADS=$NUM_USED_THREADS MKL_NUM_THREADS=$MKL_USED_THREADS OMP_DYNAMIC=$OMP_DYNAMIC MKL_DYNAMIC=$MKL_DYNAMIC /usr/bin/time -v ./$TESTNAME.ex"
if [ $MAT_TYPE == "Lap" ] 
then
	COMMAND_LINE="$COMMAND_LINE -nx $MAT_NX -ny $MAT_NY -nz $MAT_NZ -nslices $NUM_SLICES -timings $TESTNAME-$NUM_USED_THREADS-$MATTYPE_$MAT_NX-$MAT_NY-$MAT_NZ -a $A_BOUND -b $B_BOUND> run-time-$SERIAL_NUM_GEN.txt";
        
elif [ $MAT_TYPE == "MM" ] 
then
	#Setup matfile and matrix if matfile exists
	if [ -e "$EVSL_DIR/EVSL_1.0/MATRICES/matfile-$MAT_NAME" ] 
	then
		echo "Matfile for current matrix exists, so we will SYMLINK it for you."
		ln -s "$EVSL_DIR/EVSL_1.0/MATRICES/matfile-$MAT_NAME" "$FOLDER/matfile"
		ln -s "$EVSL_DIR/EVSL_1.0/MATRICES/$MAT_NAME.mtx" "$FOLDER/$MAT_NAME.mtx"
	else
		echo "Matfile for current matrix DOES NOT exist"
		echo "So will no symlik matfile OR matrix "
	fi
	COMMAND_LINE="$COMMAND_LINE > run-time-$SERIAL_NUM_GEN.txt"
fi
echo "$COMMAND_LINE" >> $FILE
chmod u+x $FILE
