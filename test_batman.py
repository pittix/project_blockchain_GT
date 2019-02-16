from math import exp, sqrt
from random import randint, random, seed
import numpy as np
# import pandas as pd
from simulator.core import G, event_queue
from simulator.layers import BatmanLayer, ApplicationLayer, Layer

# default values
LIGHT_SPEED = 299792458
PROC_TIME = 0.001


def interarrival_gen():
    while True:
        yield random() * 10


def size_gen():
    while True:
        yield randint(100, 200)


def connect_batmans(batmans, dist_lim):
    distance = np.zeros((len(batmans), len(batmans)))
    for ip1 in batmans:
        for ip2 in batmans:
            distance[ip1][ip2] = sqrt(
                (batmans[ip1].position[0] - batmans[ip2].position[0])**2
                + (batmans[ip1].position[1] - batmans[ip2].position[1])**2
            )

    for ip1 in batmans:
        # pick the N-closest nodes
        N_CLOSEST = 10
        max_idx = np.argpartition(distance[ip1, :], -N_CLOSEST)[-N_CLOSEST:]

        # ensure that they are close enough
        neigh_nodes = max_idx[(distance[ip1, max_idx] > 0)]

        for ip2 in neigh_nodes:
            p_succ = exp(-distance[ip1, ip2]/dist_lim)
            rtt = PROC_TIME + distance[ip1, ip2]/LIGHT_SPEED

            batmans[ip1].connect_to(batmans[ip2], p_succ=p_succ, rtt=rtt)
            batmans[ip2].connect_to(batmans[ip1], p_succ=p_succ, rtt=rtt)
    return batmans


def connect_apps(batmans, app_rate, stop_time):
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

                apps.append((app1, app2))
    return apps


def calc_app(batman):
    tx_bytes = 0
    rx_bytes = 0
    num_app = 0
    # for each app connected to this batman sum the number of tx/rx bytes
    for app_id in batman.app_table.values():
        this_app = Layer.all_layers[app_id]
        tx_bytes += this_app.tx_packet_size
        rx_bytes += this_app.rx_packet_size
        num_app += 1
    return (tx_bytes, rx_bytes, num_app)


def new_snapshot(batmans, args):
    selfish_count = 0
    altruistic_count = 0
    tot_tx_self = 0
    tot_rx_self = 0
    tot_tx_altr = 0
    tot_rx_altr = 0
    for ip in batmans:
        tx_bytes, rx_bytes, num_app = calc_app(batmans[ip])
        if batmans[ip].selfish is True:
            selfish_count += num_app
            tot_tx_self += tx_bytes
            tot_rx_self += rx_bytes
        else:
            altruistic_count += num_app
            tot_tx_altr += tx_bytes
            tot_rx_altr += rx_bytes

    this_snap = {
                'time': event_queue.now,
                **args,
                'altruistic_tx': tot_tx_altr,
                'altruistic_rx': tot_rx_altr,
                'selfish_tx': tot_tx_self,
                'selfish_rx': tot_rx_self,
                'selfish_num': selfish_count,
                'altruistic_num': altruistic_count
                }
    return this_snap


def update_selfishness(batmans):
    # approach 1: if neighbours are almost all altruistic, then become selfish
    # if I have a bad reputation, try gaining it
    drop_lim = BatmanLayer.drop_lim
    for bat in batmans.values():
        if bat.drop_score > drop_lim:
            bat.selfish = False
        else:
            neighbours = bat.neighbour_table.keys()
            self_neigh = [batmans[neigh].selfish for neigh in neighbours]
            if self_neigh.count(True) < 5:
                bat.selfish = True


def simulator_batman(args):
    s = args["s"]
    node_num = args["node_num"]
    dim = args["dim"]
    dist_lim = args["dist_lim"]
    app_rate = args["app_rate"]
    selfish_rate = args["selfish_rate"]
    stop_time = args["stop_time"]
    upd_time = args["update_time"]
    snapshot_interval = args["snapshot_interval"]
    BatmanLayer.drop_lim = args["drop_lim"]

    # 1) load queue for events created in simulator module
    seed(s)

    # clear global variables from previous simulation
    Layer.all_layers.clear()
    event_queue.clean()
    G.clear()

    # create a number of batman layers, corresponding to nodes

    # set deterministic number of selfish nodes: improves reliability of
    # results in small scenarios

    batmans = {
        ip: BatmanLayer(ip,
                        selfish=(random() < selfish_rate),
                        position=(dim * random(), dim * random()),
                        )
        for ip in range(node_num)
    }

    # connect each other using some channels, described using a success
    # probability and round trip time
    batmans = connect_batmans(batmans, dist_lim)

    # apps = connect_apps(batmans, app_rate=app_rate, stop_time=stop_time)

    # apps var never used. In fact I always use Layers.all_layers id_ param
    # to identify the app
    connect_apps(batmans, app_rate=app_rate, stop_time=stop_time)
    # run the simulation, until we run out of events
    # counter = 0
    snapshot_next = 0
    upd_next = 0
    snapshots = []
    while True:
        # counter += 1
        # if counter % 10000 == 0:
        #     logger.debug(event_queue.now)

        # trigger events until we run out of them
        if event_queue.next() is None:
            break
        if event_queue.now > snapshot_next:
            snapshot_next += snapshot_interval
            snapshots.append(new_snapshot(batmans, args))
        # update selfish rates
        if event_queue.now > upd_next:
            upd_next += upd_time
            update_selfishness(batmans)

    # Add last snapshot for final situation evaluation
    snapshots.append(new_snapshot(batmans, args))
    return snapshots
