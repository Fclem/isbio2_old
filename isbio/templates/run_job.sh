#!/bin/bash
echo 'Current dir is '`pwd`
# deleteing possibly existing files generated from a previous run
rm *~ *.Rout failed INCOMPLETE_RUN done r_done > /dev/null 2>&1
IN=script.r
OUT=script.r.Rout
echo -n 'Running R script...'
# Running the job
touch ./INCOMPLETE_RUN && R CMD BATCH --no-save ./$IN && touch ./done
echo ' done !'
rm ./INCOMPLETE_RUN > /dev/null 2>&1
txt="Execution halted" 
CMD=`tail -n1<./$OUT`
# check the last line of the Rout file for possible R failure
if [ "$CMD" = "$txt" ] || [ ! -f "r_done" ]; 
then
	touch ./failed
	cat $OUT
	echo 'Failure !'
	#less $OUT
	exit 120
else
	echo 'Success !'
	exit
fi
rm *~ > /dev/null 2>&1
