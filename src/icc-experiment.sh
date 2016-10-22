MAXUE=30
STEPUE=30
MAXREP=5
STEPREP=1
 
for r in `seq 0 $STEPREP $(($MAXREP - 1))`; do
	for u in `seq 30 $STEPUE $(($MAXUE))`; do
		python icc.py $r $u &
	done    
done
wait