#!/bin/bash

python -O simulator_starter.py -n $(cat nodes.txt) -s $(cat seeds.txt) \
      -d-lim $(cat dist-limits.txt) -d $(cat dimensions.txt) \
      -a $(cat app_rate.txt) -st $(cat stop.txt) -selfish $(cat selfish.txt)
# python -O test_batman.py -n 100 -s 18 -d-lim 500 -d 1000 -a 0.25 -st 100 -selfish 0.1 $
