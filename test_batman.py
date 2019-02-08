import logging
from math import exp, sqrt
from random import randint, random, seed

import networkx as nx
import numpy as np

from simulator import *

# default values
LIGHT_SPEED = 299792458
PROC_TIME = 0.001

def interarrival_gen():
    while True:
        yield random() * 10

def size_gen():
    while True:
        yield randint(100, 200)

def simulator_batman(args):
    s = args["s"]
    node_num = args["node_num"]
    dim = args["dim"]
    dist_lim = args["dist_lim"]
    app_rate = args["app_rate"]
    selfish_rate = args["selfish_rate"]
    stop_time = args["stop_time"]

    # 1) load queue for events created in simulator module
    seed(s)

    # clear global variables
    Layer.all_layers.clear()
    event_queue.clean()
    G.clear()

    # create a number of batman layers, corresponding to nodes
    batmans = {
        ip: BatmanLayer(ip,
                        selfish=(random() < selfish_rate),
                        position=(dim * random(), dim * random()))
        for ip in range(node_num)
    }

    # connect each other using some channels, described using a success
    # probability and round trip time
    distance = np.zeros((len(batmans), len(batmans)))
    for ip1 in batmans:
        for ip2 in batmans:
            distance[ip1][ip2] = sqrt(
                (batmans[ip1].position[0] - batmans[ip2].position[0])**2 +
                (batmans[ip1].position[1] - batmans[ip2].position[1])**2
            )

    for ip1 in batmans:
        # pick the N-closest nodes
        N_CLOSEST = 10
        max_idx = np.argpartition(distance[ip1, :], -N_CLOSEST)[-N_CLOSEST:]

        # ensure that they are close enough
        neigh_nodes = max_idx[ (distance[ip1, max_idx] < dist_lim) &
                               (distance[ip1, max_idx] > 0) ]

        for ip2 in neigh_nodes:
            p_succ = exp(-distance[ip1, ip2]/dist_lim)
            rtt = PROC_TIME + distance[ip1, ip2]/LIGHT_SPEED

            batmans[ip1].connect_to(batmans[ip2], p_succ=p_succ, rtt=rtt)

    # create the application for each end-to-end stream: for the simulation
    # to be reasonable, each node has to have at least one application
    apps = []
    port_no = 1000
    # ensure unique port for each app (just to play safe)

    for ip1 in batmans:
        for ip2 in batmans:
            if ip1 == ip2:
                continue
            elif random() < app_rate:
                port1 = port_no
                port2 = port_no + 1
                port_no += 10

                app1 = ApplicationLayer(interarrival_gen(),
                                        size_gen(),
                                        start_time=0,
                                        stop_time=stop_time,
                                        local_port=port1,
                                        local_ip=ip1,
                                        dst_port=port2,
                                        dst_ip=ip2)
                batmans[ip1].connect_app(app1)

                app2 = ApplicationLayer(interarrival_gen(),
                                        size_gen(),
                                        start_time=0,
                                        stop_time=stop_time,
                                        local_port=port2,
                                        local_ip=ip2,
                                        dst_port=port1,
                                        dst_ip=ip1)
                batmans[ip2].connect_app(app2)

                apps.append( (app1, app2) )

    # run the simulation, until we run out of events
    counter = 0
    try:
        while True:
            counter += 1
            if counter % 10000 == 0:
                logger.debug(event_queue.now)

            # trigger events until we run out of them
            if event_queue.next() is None:
                break
    except nx.exception.NetworkXNoPath as err:
        logger.error("Error: two nodes are not connected: ")
        logger.error("message: ", err)
        return

    # judge application layer rates
    performances = {ip: 0 for ip in batmans.keys()}
    for app1, app2 in apps:
        # node1 -> node2 communication
        performances[app1.local_ip] += app1.rx_packet_size
        performances[app2.local_ip] += app2.rx_packet_size

    # report everything to csv
    # convert parameters dictionary to a valid file name
    string_var = "-".join(map(lambda x: "{}={}".format(*x), args.items()))
    logger.debug("saving {}.csv".format(string_var))

    # save graph to file
    nx.write_gml(G, "results/{}.gml".format(string_var))

    with open("results/{}.csv".format(string_var), 'w') as csvfile:
        csvfile.write("ip,selfish,total_packet_size\n")

        for ip, size in performances.items():
            csvfile.write("{},{},{}\n".format(ip, int(batmans[ip].selfish), size))
