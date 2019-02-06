import logging
from random import randint, random, randrange

from scipy.constants import Boltzmann, pi

from simulator import *

logging.basicConfig(level=logging.DEBUG)

# 1) load queue for events created in simulator module
event_queue.clean()

## create a number of batman layers, corresponding to nodes
batmans = {
    ip: BatmanLayer(ip)
    for ip in range(1, 11)
}

## connect each other using some channels, described using a success probability
## and round trip time
RTT_n = 1
RTT_y = 0.1

p_y = 0.9
p_n = 0.7

graph = [
    # node1, node2, p_succ, rtt
    (4,  1, p_n, RTT_n),
    (4,  2, p_y, RTT_y),
    (4,  6, p_y, RTT_y),
    (4,  7, p_y, RTT_y),

    (5,  2, p_y, RTT_n),
    (5,  3, p_y, RTT_y),
    (5,  7, p_n, RTT_n),
    (5,  8, p_y, RTT_y),

    (10, 7, p_n, RTT_y),
    (10, 8, p_y, RTT_n),
    (10, 9, p_n, RTT_n),

    (7,  9, p_y, RTT_y),
    (7,  8, p_n, RTT_y),
]

channels = {}
for ip1, ip2, p_succ, rtt in graph:
    local_channels = batmans[ip1].connect_to(batmans[ip2], p_succ=p_succ, rtt=rtt)
    channels = {**channels, **local_channels}

## schedule update of neighbour tables in batman nodes
UPDATE_TIME = 10
## create a couple of application for each end-to-end stream: for the simulation
## to be reasonable, each node has to have at least one application

app_links = [
    (1, 2),
    (1, 10),

    (2, 6),
    (2, 7),

    (3, 4),
    (3, 8),

    (5, 9),

    (8, 10)
]

# store here the resulting couples
apps = []

def interarrival_gen():
    while True:
        yield random() * 10

def size_gen():
    while True:
        yield randint(100, 200)

# ensure unique port for each app (just to play safe)
port_no = 1000
for ip1, ip2 in app_links:
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

## run the simulation, until we run out of events
while True:
    # trigger events until we run out of them
    if event_queue.next() is None:
        break

## judge application layer rates
performances = { ip: 0 for ip in batmans.keys() }

for app1, app2 in apps:
    # node1 -> node2 communication
    bitrate1 = app1.tx_packet_size - app2.rx_packet_size
    performances[app1.local_ip] += bitrate1

    # node2 -> node1 communication
    bitrate2 = app2.tx_packet_size - app1.rx_packet_size
    performances[app2.local_ip] += bitrate2

print(performances)
