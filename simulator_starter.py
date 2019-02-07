import argparse
import sys

from simulator import *
from test_batman import *

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


var = vars(parser.parse_args(sys.argv[1:]))
# check that I have the same number of simulations
if (len(var["node_num"]) == len(var["s"])
    and len(var["s"]) == len(var["dim"])
    and len(var["s"]) == len(var["dist_lim"])
    and len(var["s"]) == len(var["app_rate"])):

    # run a simulation for each parameter
    for i in range(len(var["node_num"])):
        tmp_var = {
            "s": var["s"][i],
            "node_num": var["node_num"][i],
            "dim": var["dim"][i],
            "dist_lim": var["dist_lim"][i],
            "app_rate": var["app_rate"][i]
        }
        simulator_batman(**tmp_var)
