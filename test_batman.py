import logging
from math import exp, sqrt
from random import randint, random, seed
from simulator import *

# default values
NODE_NUM = 100
DIM = 1000
DISTANCE_LIM = 200
LIGHT_SPEED = 299792458
APP_CONN_RATE = 0.25
PROC_TIME = 0.001

logging.basicConfig(level=logging.ERROR)


def interarrival_gen():
    while True:
        yield random() * 10


def size_gen():
    while True:
        yield randint(100, 200)


def simulator_batman(s=1, node_num=NODE_NUM, dim=DIM, dist_lim=DISTANCE_LIM,
                app_rate=APP_CONN_RATE):
    # 1) load queue for events created in simulator module
    seed(s)

    event_queue.clean()

    # create a number of batman layers, corresponding to nodes
    batmans = {
        ip: BatmanLayer(ip)
        for ip in range(NODE_NUM)
    }

    # connect each other using some channels, described using a success probability
    # and round trip time
    node_positions = {}
    channels = {}
    for ip in batmans.keys():
        node_positions[ip] = (dim*random(), dim*random())

    for ip1 in node_positions:
        for ip2 in node_positions:
            if ip1 == ip2:
                continue
            dist = sqrt((node_positions[ip1][0] - node_positions[ip2][0])**2
                        + (node_positions[ip1][1]
                         - node_positions[ip2][1])**2)
            if dist < dist_lim:
                p_succ = exp(-dist/dist_lim)
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
            elif random() < app_rate:
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
    # plt.show()

    # run the simulation, until we run out of events
    counter = 0
    while True:
        if counter % 10000 == 0:
            print(event_queue.now)
        counter += 1

        # trigger events until we run out of them
        if event_queue.next() is None:
            break

    # judge application layer rates
    performances = {ip: 0 for ip in batmans.keys()}
    # cur_time = event_queue.now
    for app1, app2 in apps:
        # node1 -> node2 communication
        # print('TX: ', app1.id_, ' -->', app2.id_, ' Rate ', app1.rx_packet_size/cur_time)
        # print('TX: ', app2.id_, ' -->', app1.id_, ' Rate ', app2.rx_packet_size/cur_time)
        performances[app1.local_ip] += app1.rx_packet_size
        performances[app2.local_ip] += app2.rx_packet_size

    simulation_filename = "results/{}_{}.csv".format(s, node_num)
    with open(simulation_filename, 'w') as csvfile:
        for ip, size in performances.items():
            csvfile.write("{},{}\n".format(ip, size))
