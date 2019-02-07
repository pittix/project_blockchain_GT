#!/bin/bash

FAILED=0

python -O test_batman.py -n 100 -s 17 -d-lim 500 -d 1000 -a 0.25 -st 100 -selfish 0.1 &
python -O test_batman.py -n 100 -s 18 -d-lim 500 -d 1000 -a 0.25 -st 100 -selfish 0.1 &

## wait for all the job to finish
for job in `jobs -p`
do
    wait $job || let "FAILED+=1"
done

echo "$FAILED processes failed"
