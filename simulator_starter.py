import argparse
import multiprocessing as mp
import sys
import time

import numpy as np

from simulator import *
from test_batman import *

## setup simulation parameters

# fixed parameters, describing topology
scenarios = [
    { 'dim': 100, 'dist_lim': 100, 'node_num': 10, 'stop_time': 100 },
    { 'dim': 500, 'dist_lim': 400, 'node_num': 100, 'stop_time': 100 }
]

# repeat each combination n times
seeds = list(range(100))

# tunable parameters
selfish_rates = np.linspace(0.1, 0.6, num=10)
app_rates = np.linspace(0.01, 0.02, num=10)

print("Total number of combinations: {}".format(
    len(scenarios) * len(seeds) * len(selfish_rates) * len(app_rates)
))

def combinations():
    for scenario in scenarios:
        for selfish_rate in selfish_rates:
            for app_rate in app_rates:
                for seed in seeds:
                    yield { **scenario,
                            'selfish_rate': selfish_rate,
                            'app_rate': app_rate,
                            's': seed
                    }

## setup pool of workers

available_threads = mp.cpu_count() - 1
p = mp.Pool(available_threads)

p.map(simulator_batman, combinations())
