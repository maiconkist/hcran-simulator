MAXUE=5
STEPUE=5
MAXREP=2
STEPREP=1
 
for r in `seq 0 $STEPREP $(($MAXREP - 1))`; do
	for u in `seq 5 $STEPUE $(($MAXUE))`; do
		python icc.py $r $u &
	done    
done
wait