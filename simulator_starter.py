from simulator import *
from test_batman import *
import argparse
import sys
import multiprocessing as mp
import time
parser = argparse.ArgumentParser("Simulate batman")
parser.add_argument('-n', help='number of nodes', action='append',
                dest='node_num', type=int, nargs='+')
parser.add_argument('-s', help='seed', action='append', dest='s',
                    type=int, nargs='+')
parser.add_argument('-d-lim', help='distance limit', action='append',
                dest='dist_lim', type=float, nargs='+')
parser.add_argument('-d', help='length of the square', action='append',
                dest='dim', type=float, nargs='+')
parser.add_argument('-a', help='rate of connection between apps', action='append',
                dest='app_rate', type=float, nargs='+')

available_threads = mp.cpu_count() - 1

var = vars(parser.parse_args(sys.argv[1:]))
# extract line parameters. they are in a nested list [[p1,p2]]
var = {
    "s": var["s"][0],
    "node_num": var["node_num"][0],
    "dim": var["dim"][0],
    "dist_lim": var["dist_lim"][0],
    "app_rate": var["app_rate"][0]
    }
if(len(var) > available_threads):
    p = mp.Pool(available_threads)
else:
    p = mp.Pool(len(var))

failures = 0
results = []


def start_new_thread():
    global available_threads, failures, results
    if len(var["s"]) > 0:  # at least another thread can start
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
        try:
            res = p.apply_async(simulator_batman, (tmp_var,), callback=process_finished)
            results.append(res)
        except Exception as e:
            print("Error:")
            print(e)
            failures += 1
        available_threads -= 1
    else:
        pass


def process_finished(res):
    global available_threads, results
    available_threads += 1
    start_new_thread()


# check that I have the same number of simulations
if (len(var["node_num"]) == len(var["s"])
        and len(var["s"]) == len(var["dim"])
        and len(var["s"]) == len(var["dist_lim"])
        and len(var["s"]) == len(var["app_rate"])):
    while(available_threads > 0 and len(var["s"]) > 0):
        start_new_thread()
    # avoid program from finishing until all processes are done
    while(len(results) > 0):
        time.sleep(10)  # wait 10 seconds before re-checking
        finished = [x.ready() for x in results]
        # remove finished results
        results = [res for i, res in enumerate(results) if not finished[i]]

print("processes failed: ", failures)
