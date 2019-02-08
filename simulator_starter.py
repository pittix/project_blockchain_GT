import argparse
import multiprocessing as mp
import sys
import time

from simulator import *
from test_batman import *

parser = argparse.ArgumentParser("Simulate batman")

parser.add_argument('-n',
                    help='number of nodes',
                    action='append',
                    dest='node_num',
                    type=int,
                    nargs='+')

parser.add_argument('-s',
                    help='seed',
                    action='append',
                    dest='s',
                    type=int,
                    nargs='+')

parser.add_argument('-d-lim',
                    help='distance limit',
                    action='append',
                    dest='dist_lim',
                    type=float,
                    nargs='+')

parser.add_argument('-d',
                    help='length of the square',
                    action='append',
                    dest='dim',
                    type=float,
                    nargs='+')

parser.add_argument('-a',
                    help='rate of connection between apps',
                    action='append',
                    dest='app_rate',
                    type=float,
                    nargs='+')

parser.add_argument('-selfish',
                    help='fraction of selfish users',
                    dest='selfish_rate',
                    type=float,
                    nargs='+',
                    action='append')

parser.add_argument('-st',
                    help='Time packet generation has to stop',
                    dest='stop_time',
                    type=float,
                    nargs='+',
                    action='append')


var = vars(parser.parse_args(sys.argv[1:]))
var = {key: value[0] for key, value in var.items()}
sim_num = len(var)
print("Number of simulations: ", sim_num)

available_threads = mp.cpu_count() - 1
if(len(var) > available_threads):
    p = mp.Pool(available_threads)
else:
    p = mp.Pool(len(var))

failures = 0
results = []

def start_new_thread():
    global available_threads, failures, results

    if len(var["s"]) > 0:  # at least another thread can start
        current_var = { key: value[0] for key, value in var.items() }

        # remove the item from the queue list
        for param in var:
            var[param] = var[param][1:]

        # start the thread and program a new start when the function ends
        res = p.apply_async(simulator_batman, (current_var,),
                            callback=process_finished,
                            error_callback=process_error)
        results.append(res)
        available_threads -= 1
    else:
        pass

def process_finished(res):
    global available_threads

    available_threads += 1
    start_new_thread()

def process_error(err):
    global failures

    print("An error occoured: ")
    print("class: ", err.__class__)
    print("message: ", err)
    failures += 1

# check that I have the same number of simulations
if len(var["node_num"]) == len(var["s"]) and \
   len(var["s"]) == len(var["dim"])      and \
   len(var["s"]) == len(var["dist_lim"]) and \
   len(var["s"]) == len(var["app_rate"]):

    while available_threads > 0 and len(var["s"]) > 0:
        start_new_thread()

    # avoid program from finishing until all processes are done
    while len(results) > 0:
         # wait 10 seconds before re-checking
        time.sleep(10)
        finished = [x.ready() for x in results]

        # remove finished results
        results = [res for i, res in enumerate(results) if not finished[i]]
        print("checking how many processes are running: ", len(results))
else:
    print("Invalid params: arrays have different lengths")

print("processes failed: ", failures, " out of ", sim_num, " simulations")
