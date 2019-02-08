#!/bin/bash

app_rate="  0.2 0.1 "
dimensions="100 100 "
dist_lims=" 40   50 "
nodes="     101 200 "
seeds="     1    22 "
selfish="   0.2 0.3 "
stop="      100 100 "

python -O simulator_starter.py \
       -n $nodes \
       -s $seeds \
       -d-lim $dist_lims \
       -d $dimensions \
       -a $app_rate \
       -st $stop \
       -selfish $selfish
