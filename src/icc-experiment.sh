MAXUE=100
STEPUE=10
MAXREP=5
STEPREP=1
 
for r in `seq 0 $STEPREP $(($MAXREP - 1))`; do
	for u in `seq 10 $STEPUE $(($MAXUE))`; do
		python icc.py $r $u &
	done    
done
wait