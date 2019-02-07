from simulator import *
from test_batman import *
import argparse
import sys
import multiprocessing as mp
parser = argparse.ArgumentParser("Simulate batman")
parser.add_argument('-n', help='number of nodes', action='append',
                dest='node_num', type=int)
parser.add_argument('-s', help='seed', action='append', dest='s', type=int)
parser.add_argument('-d-lim', help='distance limit', action='append',
                dest='dist_lim', type=int)
parser.add_argument('-d', help='length of the square', action='append',
                dest='dim', type=int)
parser.add_argument('-a', help='rate of connection between apps', action='append',
                dest='app_rate', type=float)

available_threads = mp.cpu_count() - 1

var = vars(parser.parse_args(sys.argv[1:]))
if(len(var) > available_threads):
    p = mp.Pool(available_threads)
else:
    p = mp.Pool(len(var))


def start_new_thread():
    nonlocal available_threads
    if len(var) > 0:  # at least another thread can start
        tmp_var = {
            "s": var["s"][0],
            "node_num": var["node_num"][0],
            "dim": var["dim"][0],
            "dist_lim": var["dist_lim"][0],
            "app_rate": var["app_rate"][0]
            }
        # remove the item from the queue list
        var["s"] = var["s"][1:]
        var["node_num"] = var["node_num"][1:]
        var["dim"] = var["dim"][1:]
        var["dist_lim"] = var["dist_lim"][1:]
        var["app_rate"] = var["app_rate"][1:]
        # start the thread and program a new start when the function ends
        p.apply_async(simulator_batman, **tmp_var, callback=process_finished)
        available_threads -= 1
    else:
        pass


def process_finished():
    nonlocal available_threads
    available_threads += 1
    start_new_thread()


# check that I have the same number of simulations
if (len(var["node_num"]) == len(var["s"])
        and len(var["s"]) == len(var["dim"])
        and len(var["s"]) == len(var["dist_lim"])
        and len(var["s"]) == len(var["app_rate"])):
    while(available_threads > 0):
        start_new_thread()
