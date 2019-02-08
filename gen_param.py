import os, sys
import numpy as np
SELFISH_MIN = 0.1
SELFISH_MAX = 0.3  # 0.6
SELFISH_STEP = 0.1

APP_R_MIN = 0.01
APP_R_MAX = 0.1  # 0.2
APP_R_STEP = 0.01

NODE_MIN = 10
NODE_MAX = 50  # 100
NODE_STEP = 10

DIST_LIM_MIN = 25
DIST_LIM_MAX = 100  # 500
DIST_LIM_STEP = 25  # 50

DIM_MIN = 50
DIM_MAX = 200  # 1000
DIM_STEP = 50  # 100

STOP_MIN = 10
STOP_MAX = 50  # 100
STOP_STEP = 10
# arrays
nodes = []
selfishs = []
app_rates = []
dist_lims = []
dims = []
stops = []

# generate the couples
for node in np.arange(NODE_MIN, NODE_MAX, NODE_STEP):
    for selfish in np.arange(SELFISH_MIN, SELFISH_MAX, SELFISH_STEP):
        for app_rate in np.arange(APP_R_MIN, APP_R_MAX, APP_R_STEP):
            for dist_lim in np.arange(DIST_LIM_MIN, DIST_LIM_MAX, DIST_LIM_STEP):
                for dim in np.arange(DIM_MIN, DIM_MAX, DIM_STEP):
                    for stop in np.arange(STOP_MIN, STOP_MAX, STOP_STEP):
                        nodes.append(node)
                        selfishs.append(selfish)
                        app_rates.append(app_rate)
                        dist_lims.append(dist_lim)
                        dims.append(dim)
                        stops.append(stop)

print(len(stops))

seed_value = int(input("set the seed for this run:"))
#seed array with same length
seeds = [seed_value for i in range(len(nodes))]

seed_txt = " ".join(str(x) for x in seeds)
nodes_txt = " ".join(str(x) for x in nodes)
dims_txt = " ".join(str(x) for x in dims)
selfishs_txt = " ".join(str(x) for x in selfishs)
stops_txt = " ".join(str(x) for x in stops)
dist_lims_txt = " ".join(str(x) for x in dist_lims)
app_rates_txt = " ".join(str(x) for x in app_rates)

command_1 = "python -O simulator_starter.py -s {} -n {} -d {}".format(
        seed_txt,
        nodes_txt,
        dims_txt
        )
command_2 = " -d-lim {} -a {} -st {} -selfish {}".format(
        dist_lims_txt,
        app_rates_txt,
        stops_txt,
        selfishs_txt
        )
os.system(command_1+command_2)
