# import argparse
import logging
import multiprocessing as mp
import subprocess
# import sys
import time
import datetime

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
    {'dim': 300, 'dist_lim': 100, 'node_num': 10, 'stop_time': 100},
    # { 'dim': 400, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 },
    # { 'dim': 500, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 },
    # { 'dim': 600, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 },
    # { 'dim': 800, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 },
    # { 'dim': 1000, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100 }
]

# repeat each combination n times
seeds = list(range(1000, 1010))

# tunable parameters
selfish_rates = [0.1]
app_rates = [0.1]
snapshots = [0.1]
updates = [0.2]
tot_sim = len(scenarios) * len(seeds) * len(selfish_rates) * len(app_rates)
tot_sim *= len(snapshots) * len(updates)
print("Total number of combinations: {}".format(tot_sim))


def combinations():
    for scenario in scenarios:
        for selfish_rate in selfish_rates:
            for app_rate in app_rates:
                for seed in seeds:
                    for snapshot_interval in snapshots:
                        for update_time in updates:
                            if update_time > snapshot_interval:
                                continue
                            yield {
                                **scenario,
                                'selfish_rate': selfish_rate,
                                'app_rate': app_rate,
                                's': seed,
                                'update_time': update_time,
                                'snapshot_interval': snapshot_interval
                                }


# init parameter generator
combos = combinations()
print(combos)
# setup pool of workers
available_threads = mp.cpu_count()  # 32  # se in coda dentro 'Blade'
p = mp.Pool(available_threads)
# prepare backup
time_str = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
# clean old results
mv_str = "mv results/simulation_results.hdf5 \
            results/simulation_results.hdf5.bak_{}".format(time_str)
subprocess.call(mv_str, shell=True)
store = pd.HDFStore("results/simulation_results.hdf5")
results = []
failures = 0


def start_new_thread():
    global available_threads, combos, results, p
    print("entered start_new_thread")
    a = True
    try:
        while a:
            tmp_var = next(combos)
            a = False
            print("tmp var : ", tmp_var)
    except StopIteration as e:
        print("error:", e)
        time.sleep(3)
        return
    if tmp_var is None:
        print("reached stop iteration")
        # finished processes
        available_threads -= 1  # case num_sim < available_threads
        return
        # start the thread and program a new start when the function ends
    print("starting process")
    res = p.apply_async(
                        simulator_batman,
                        (tmp_var,),
                        callback=process_finished,
                        error_callback=process_error
                        )
    print("started ", res)
    results.append(res)
    available_threads -= 1


def process_finished(res):
    global available_threads
    store.append(
                'results',
                pd.DataFrame.from_dict(res),
                format='t',
                data_columns=True
                )
    available_threads += 1
    start_new_thread()


def process_error(err):
    global failures
    print("An error occoured: ")
    print("class: ", err.__class__)
    print("message: ", err)
    failures += 1
    start_new_thread()


# check that I have the same number of simulations
while(available_threads > 0):
    print("Starting new thread")
    start_new_thread()
    print("Started new thread")
    # avoid program from finishing until all processes are done
time.sleep(10)  # wait 10 seconds before re-checking
while(len(results) > 0):
    time.sleep(10)  # wait 10 seconds before re-checking
    finished = [x.ready() for x in results]
    # remove finished results
    results = [res for i, res in enumerate(results) if not finished[i]]
    print("checking how many processes are running: ", len(results))

store.close()
