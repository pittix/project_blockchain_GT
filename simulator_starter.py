# import argparse
import logging
import multiprocessing as mp
# import subprocess
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
    {'dim': 100, 'dist_lim': 100, 'node_num': 20, 'stop_time': 100},
    {'dim': 300, 'dist_lim': 100, 'node_num': 20, 'stop_time': 100},
    {'dim': 100, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100},
    {'dim': 300, 'dist_lim': 100, 'node_num': 100, 'stop_time': 100},
    {'dim': 100, 'dist_lim': 100, 'node_num': 50, 'stop_time': 100},
    {'dim': 300, 'dist_lim': 100, 'node_num': 50, 'stop_time': 100},
    {'dim': 100, 'dist_lim': 100, 'node_num': 200, 'stop_time': 100},
    {'dim': 300, 'dist_lim': 100, 'node_num': 200, 'stop_time': 100},
]

# repeat each combination n times
seeds = list(range(1000, 1100))

# tunable parameters
selfish_rates = [0.1, 0.3, 0.5, 0.7]
app_rates = np.arange(0.03, 0.08, 0.02)
np.append(app_rates, np.arange(0.1, 0.6, 0.2))
updates = [1, 2, 3]
drop_scores = [5, 10, 15]
# a = np.linspace(0, 0.5, num=10)
tot_sim = len(scenarios) * len(seeds) * len(selfish_rates) * len(app_rates)
tot_sim *= len(updates)*len(drop_scores)
print("Total number of combinations: {}".format(tot_sim))


def combinations():
    for scenario in scenarios:
        for selfish_rate in selfish_rates:
            for app_rate in app_rates:
                for seed in seeds:
                    for update_time in updates:
                        for score_lim in drop_scores:
                            yield {
                                **scenario,
                                'selfish_rate': selfish_rate,
                                'app_rate': app_rate,
                                's': seed,
                                'update_time': update_time,
                                'drop_lim': score_lim
                                }


# init parameter generator
combos = combinations()
# setup pool of workers
available_threads = mp.cpu_count()  # 32  # se in coda dentro 'Blade'
p = mp.Pool(available_threads)
# prepare backup
time_str = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
# clean old results
# mv_str = "mv results/simulation_results.hdf5 \
#             results/simulation_results.hdf5.bak_{}".format(time_str)
# subprocess.call(mv_str, shell=True)
store = pd.HDFStore("/home/pittaroa/project_blockchain_GT/results/simulation_results_0_{}.hdf5".format(time_str))
results = []
failures = 0
count_ended = 0
num_stores = 1


def start_new_thread():
    global available_threads, combos, results, p
    try:
        tmp_var = next(combos)
        # start the thread and program a new start when the function ends
        res = p.apply_async(
                            simulator_batman,
                            (tmp_var,),
                            callback=process_finished,
                            error_callback=process_error
                            )
        results.append(res)
        available_threads -= 1
    except StopIteration:
        available_threads -= 1
        return


def process_finished(res):
    global available_threads, count_ended, store, num_stores, time_str
    store.append(
                'results',
                pd.DataFrame.from_records(res),
                format='t',
                data_columns=True
                )
    available_threads += 1
    count_ended += 1
    # save into smaller files to avoid huge RAM consumption and storing data if
    # failure happens meanwhile
    if count_ended % 10000 == 0:
        store.close()
        store = pd.HDFStore("/home/pittaroa/project_blockchain_GT/results/simulation_results_{}_{}.hdf5".format(num_stores, time_str))
        num_stores += 1
    start_new_thread()


def process_error(err):
    global failures, count_ended
    print("An error occoured: ")
    print("class: ", err.__class__)
    print("message: ", err)
    print("Traceback:", err.__traceback__)
    failures += 1
    count_ended += 1
    start_new_thread()


# check that I have the same number of simulations
while(available_threads > 0):
    start_new_thread()
    # avoid program from finishing until all processes are done
time.sleep(1)  # wait 1 second before re-checking

with open("/home/pittaroa/Public-Htdocs/progress.txt", "w") as file:
    file.write("Started {} sim at time {}".format(tot_sim, time_str))

while(len(results) > 0):
    time.sleep(10)  # wait 10 seconds before re-checking
    finish = [x.ready() for x in results]
    # remove finished results
    # update results list, minding that the list can increase in size
    new_res = [r for i, r in enumerate(results[:len(finish)]) if not finish[i]]
    results = new_res + results[len(finish):]
    # print("checking how many processes are running: ", len(results))
    if count_ended % 100 == 0:
        with open("/home/pittaroa/Public-Htdocs/progress.txt", "w") as file:
            file.write("Done {} sim out of {} \n".format(count_ended, tot_sim))
            file.write("Progress done: {:.3%}".format(count_ended/tot_sim))
store.close()
with open("/home/pittaroa/Public-Htdocs/progress.txt", "w") as file:
    time_str = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
    file.write("Simulation ended with {} \
                failures at {}".format(failures, time_str))
