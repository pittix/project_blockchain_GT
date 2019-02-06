import logging
from random import randint, random, randrange, seed

import matplotlib.pyplot as plt
from scipy.constants import Boltzmann, pi
from math import sqrt, exp
from simulator import *

seed(14)
NODE_NUM = 100
DIM = 10000
DISTANCE_LIM = 200
LIGHT_SPEED = 299792458
APP_CONN_RATE = 0.25
logging.basicConfig(level=logging.DEBUG)

# 1) load queue for events created in simulator module
event_queue.clean()

## create a number of batman layers, corresponding to nodes
batmans = {
    ip: BatmanLayer(ip)
    for ip in range(NODE_NUM)
}

## connect each other using some channels, described using a success probability
## and round trip time
RTT_n = 1
RTT_y = 0.1

p_y = 0.9
p_n = 0.7
node_positions = {}
channels = {}
for ip in batmans.keys():
    node_positions[ip] = (DIM*random(), DIM*random())

for ip1 in node_positions:
    for ip2 in node_positions:
        if ip1 == ip2:
            continue
        dist = sqrt((node_positions[ip1][0] - node_positions[ip2][0])**2 +
                    (node_positions[ip1][1] -
                     node_positions[ip2][1])**2)
        if dist < DISTANCE_LIM:
            p_succ = exp(-dist/DISTANCE_LIM)
            rtt = 0.001 + dist/LIGHT_SPEED
            local_channels = batmans[ip1].connect_to(batmans[ip2], p_succ=p_succ, rtt=rtt)
            channels = {**channels, **local_channels}

## schedule update of neighbour tables in batman nodes
UPDATE_TIME = 10
## create a couple of application for each end-to-end stream: for the simulation
## to be reasonable, each node has to have at least one application

apps = []
port_no = 1000
def interarrival_gen():
    while True:
        yield random() * 10

def size_gen():
    while True:
        yield randint(100, 200)

# ensure unique port for each app (just to play safe)

for ip1 in node_positions:
    for ip2 in node_positions:
        if ip1 == ip2:
            continue
        elif random() < APP_CONN_RATE:
            port1 = port_no
            port2 = port_no + 1
            port_no += 10

            app1 = ApplicationLayer(interarrival_gen(),
                                    size_gen(),
                                    start_time=0,
                                    stop_time=100,
                                    local_port=port1,
                                    local_ip=ip1,
                                    dst_port=port2,
                                    dst_ip=ip2)
            batmans[ip1].connect_app(app1)

            app2 = ApplicationLayer(interarrival_gen(),
                                    size_gen(),
                                    start_time=0,
                                    stop_time=100,
                                    local_port=port2,
                                    local_ip=ip2,
                                    dst_port=port1,
                                    dst_ip=ip1)
            batmans[ip2].connect_app(app2)

            apps.append( (app1, app2) )

nx.draw(G, with_labels=True, pos=node_positions)
plt.show()

## run the simulation, until we run out of events
while True:
    # trigger events until we run out of them
    if event_queue.next() is None:
        break

## judge application layer rates
performances = { ip: 0 for ip in batmans.keys() }
cur_time = event_queue.now
for app1, app2 in apps:
    # node1 -> node2 communication
    print('TX: ', app1.id_, ' -->', app2.id_, ' Rate ', app1.rx_packet_size/cur_time)
    print('TX: ', app2.id_, ' -->', app1.id_, ' Rate ', app2.rx_packet_size/cur_time)
    performances[app1.local_ip] += app1.rx_packet_size
    performances[app2.local_ip] += app2.rx_packet_size

print(performances)
