# import argparse
import logging
import multiprocessing as mp
import subprocess
# import sys
# import time

# import h5py
import numpy as np
import pandas as pd
# from simulator import
from test_batman import simulator_batman

logging.basicConfig(level=logging.INFO)

# setup simulation parameters

# fixed parameters, describing topology
scenarios = [
    # { 'dim': 100, 'dist_lim': 100, 'node_num': 10, 'stop_time': 100 },
    # { 'dim': 200, 'dist_lim': 100, 'node_num': 10, 'stop_time': 100 },
    # { 'dim': 300, 'dist_lim': 100, 'node_num': 10, 'stop_time': 100 },
    # { 'dim': 100, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 },
    # { 'dim': 200, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 },
    {'dim': 300, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100},
    # { 'dim': 400, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 },
    # { 'dim': 500, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 },
    # { 'dim': 600, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 },
    # { 'dim': 800, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 },
    # { 'dim': 1000, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 }
]

# repeat each combination n times
seeds = list(range(1000, 1010))

# tunable parameters
selfish_rates = np.linspace(0.1, 0.7, num=10)
app_rates = [0.1]

print("Total number of combinations: {}".format(
    len(scenarios) * len(seeds) * len(selfish_rates) * len(app_rates)
))


def combinations():
    for scenario in scenarios:
        for selfish_rate in selfish_rates:
            for app_rate in app_rates:
                for seed in seeds:
                    yield {
                        **scenario,
                        'selfish_rate': selfish_rate,
                        'app_rate': app_rate,
                        's': seed
                        }


# setup pool of workers
available_threads = mp.cpu_count()
p = mp.Pool(available_threads)

# clean old results
subprocess.call("""mv results/simulation_results.hdf5
                 results/simulation_results.hdf5.bak""", shell=True)
subprocess.call("rm -rf /tmp/log_files/", shell=True)

store = pd.HDFStore("results/simulation_results.hdf5")

for result in p.map(simulator_batman, combinations()):
    store.append(
                'results',
                pd.DataFrame.from_dict(result),
                format='t',
                data_columns=True
                )

store.close()
