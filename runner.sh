#!/bin/bash

python -O simulator_starter.py \
       -n $(cat simulator_params/ nodes.txt) \
       -s $(cat simulator_params/ seeds.txt) \
       -d-lim $(cat simulator_params/ dist-limits.txt) \
       -d $(cat simulator_params/ dimensions.txt) \
       -a $(cat simulator_params/ app_rate.txt) \
       -st $(cat simulator_params/ stop.txt) \
       -selfish $(cat simulator_params/ selfish.txt)
