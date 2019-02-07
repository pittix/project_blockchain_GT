import argparse
import logging
import sys
from math import exp, sqrt
from random import randint, random, seed

from simulator import *

# default values
LIGHT_SPEED = 299792458
PROC_TIME = 0.001

logging.basicConfig(level=logging.INFO)

# load configuration
parser = argparse.ArgumentParser("Simulate batman")

parser.add_argument('-n',
                    help='number of nodes',
                    dest='node_num',
                    default=100,
                    type=int)

parser.add_argument('-s',
                    help='seed',
                    dest='s',
                    type=int)

parser.add_argument('-d-lim',
                    help='distance limit',
                    default=200,
                    dest='dist_lim',
                    type=int)

parser.add_argument('-d',
                    help='length of the square',
                    dest='dim',
                    default=1000,
                    type=int)

parser.add_argument('-a',
                    help='rate of connection between apps',
                    dest='app_rate',
                    default=0.25,
                    type=float)


parser.add_argument('-selfish',
                    help='fraction of selfish users',
                    dest='selfish_rate',
                    default=0.1,
                    type=float)

parser.add_argument('-st',
                    help='Time packet generation has to stop',
                    dest='stop_time',
                    default=100,
                    type=float)

var = vars(parser.parse_args(sys.argv[1:]))

def interarrival_gen():
    while True:
        yield random() * 10

def size_gen():
    while True:
        yield randint(100, 200)

# 1) load queue for events created in simulator module
seed(var['s'])

event_queue.clean()

# create a number of batman layers, corresponding to nodes
batmans = {
    ip: BatmanLayer(ip, selfish=(random() < var['selfish_rate']))
    for ip in range(var['node_num'])
}

# connect each other using some channels, described using a success probability
# and round trip time
node_positions = {}
channels = {}
for ip in batmans.keys():
    node_positions[ip] = (var['dim'] * random(), var['dim'] * random())

for ip1 in node_positions:
    for ip2 in node_positions:
        if ip1 == ip2:
            continue

        dist = sqrt( (node_positions[ip1][0] - node_positions[ip2][0])**2 +
                     (node_positions[ip1][1] - node_positions[ip2][1])**2 )

        if dist < var['dist_lim']:
            p_succ = exp(-dist/var['dist_lim'])
            rtt = PROC_TIME + dist/LIGHT_SPEED

            local_channels = batmans[ip1].connect_to(batmans[ip2],
                                                     p_succ=p_succ, rtt=rtt)

            channels = {**channels, **local_channels}

# create the application for each end-to-end stream: for the simulation
# to be reasonable, each node has to have at least one application

apps = []
port_no = 1000

# ensure unique port for each app (just to play safe)

for ip1 in node_positions:
    for ip2 in node_positions:
        if ip1 == ip2:
            continue
        elif random() < var['app_rate']:
            port1 = port_no
            port2 = port_no + 1
            port_no += 10

            app1 = ApplicationLayer(interarrival_gen(),
                                    size_gen(),
                                    start_time=0,
                                    stop_time=var['stop_time'],
                                    local_port=port1,
                                    local_ip=ip1,
                                    dst_port=port2,
                                    dst_ip=ip2)
            batmans[ip1].connect_app(app1)

            app2 = ApplicationLayer(interarrival_gen(),
                                    size_gen(),
                                    start_time=0,
                                    stop_time=var['stop_time'],
                                    local_port=port2,
                                    local_ip=ip2,
                                    dst_port=port1,
                                    dst_ip=ip1)
            batmans[ip2].connect_app(app2)

            apps.append( (app1, app2) )

# run the simulation, until we run out of events
counter = 0
while True:
    if counter % 10000 == 0:
        logger.info("{} has reached time {}"\
                    .format(var, event_queue.now))
    counter += 1

    # trigger events until we run out of them
    if event_queue.next() is None:
        break

# judge application layer rates
performances = { ip: 0 for ip in batmans.keys() }

for app1, app2 in apps:
    # node1 -> node2 communication
    performances[app1.local_ip] += app1.rx_packet_size
    performances[app2.local_ip] += app2.rx_packet_size

# report everything to csv

# convert parameters dictionary to a valid file name
string_var = "_".join(map(lambda x: "{}-{}".format(*x), var.items()))

with open("results/{}.csv".format(string_var), 'w') as csvfile:
    csvfile.write("ip,selfish,total_packet_size\n")

    for ip, size in performances.items():
        csvfile.write("{},{},{}\n".format(ip, batmans[ip].selfish, size))
