import os, sys
SELFISH_MIN = 0.1
SELFISH_MAX = 0.6
SELFISH_STEP = 0.1

APP_R_MIN = 0.01
APP_R_MAX = 0.02
APP_R_STEP = 0.1

NODE_MIN = 10
NODE_MAX = 100
NODE_STEP = 10

DIST_LIM_MIN = 25
DIST_LIM_MAX = 500
DIST_LIM_STEP = 25

DIM_MIN = 50
DIM_MAX = 1000
DIM_STEP = 50

STOP_MIN = 10
STOP_MAX = 100
STOP_STEP = 10
# arrays
nodes = []
selfishs = []
app_rates = []
dist_lims = []
dims = []
stops = []

# generate the couples
for node in range(NODE_MIN, NODE_MIN, NODE_STEP):
    for selfish in range(SELFISH_MIN, SELFISH_MAX, SELFISH_STEP):
        for app_rate in range(APP_R_MIN, APP_R_MAX, APP_R_STEP):
            for dist_lim in range(DIST_LIM_MIN, DIST_LIM_MAX, DIST_LIM_STEP):
                for dim in range(DIM_MIN, DIM_MAX, DIM_STEP):
                    for stop in range(STOP_MIN, STOP_MAX, STOP_STEP):
                        nodes.append(node)
                        selfishs.append(selfish)
                        app_rates.append(app_rate)
                        dist_lims.append(dist_lim)
                        dims.append(dim)
                        stops.append(stop)

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

command_1 = "python simulator_starter.py -s {} -n {} -d {}".format(
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
