#!/bin/bash

app_rate   = "0.05 0.1 0.05 0.1 0.05 0.1 0.05 0.1 0.05 0.1 0.05 0.1 0.05 0.1 0.05 0.1"
dimensions = "100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 "
dist_lims  = "40   50 40   50 40   50 40   50  40   50 40   50 40   50 40   50 "
nodes      = "100 200 100 200 100 200 100 200 100 200 100 200 100 200 100 200"
seeds      = "10  10  10  10  20  20  20  20 10  10  10  10  20  20  20  20 "
selfish    = "0.2 0.3 0.2 0.3 0.2 0.3 0.2 0.3 0.4 0.5 0.4 0.5 0.4 0.5 0.4 0.5"
stop       = "100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100"

seeds2     = "101  110  110  110  210  210  210  210 101  110  110  110  210  210  210  210"

python -O simulator_starter.py \
       -n $nodes \
       -s $seeds \
       -d-lim $dist_lims \
       -d $dimensions \
       -a $app_rate \
       -st $stop \
       -selfish $selfish
       python -O simulator_starter.py \
              -n $nodes \
              -s $seeds2 \
              -d-lim $dist_lims \
              -d $dimensions \
              -a $app_rate \
              -st $stop \
              -selfish $selfish
