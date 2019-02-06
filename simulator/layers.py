import logging
from math import sqrt
from random import random

from numpy.random import geometric
from scipy.constants import Boltzmann, pi
from scipy.special import erfc

from .core import *

event_queue = EventQueue()


class Layer(Base):
    # static class variables
    last_layer_id = 0
    all_layers = {}

    def __init__(self):
        # set unique id
        Layer.last_layer_id += 1
        self.id_ = Layer.last_layer_id

        self.lower_layers_id = []
        self.upper_layers_id = []

        # store in a dict all Layers created, in order to look them up by id
        Layer.all_layers[self.id_] = self

    @logthis(logging.INFO)
    def send_up(self, packet, upper_layer_id=None):
        if len(self.upper_layers_id) == 0:
            raise ValueError("Layer {} has no upper layers!".format(self))

        # set first upper layer as default one
        if not upper_layer_id:
            upper_layer_id = self.upper_layers_id[0]

        # event is immediate, fire it now without passing through event queue
        upper_layer = Layer.all_layers[upper_layer_id]
        upper_layer.recv_from_down(packet, self.id_)

    @logthis(logging.INFO)
    def send_down(self, packet, lower_layer_id=None):
        if len(self.lower_layers_id) == 0:
            raise ValueError("Layer {} has no lower layers!".format(self))

        # set first lower layer as default one
        if not lower_layer_id:
            lower_layer_id = self.lower_layers_id[0]

        # event is immediate, fire it now without passing through event queue
        lower_layer = Layer.all_layers[lower_layer_id]
        lower_layer.recv_from_up(packet, self.id_)

    @logthis(logging.DEBUG)
    def connect_upper_layer(self, upper_layer, **kwargs):
        # this function always connects upper layers
        # to lower layers, by convention
        self.upper_layers_id.append(upper_layer.id_)

        # add self layer id_ to upper layer (connect both ways)
        upper_layer.lower_layers_id.append(self.id_)

    def recv_from_up(self, packet, upper_layer_id):
        raise NotImplemented

    def recv_from_down(self, packet, lower_layer_id):
        raise NotImplemented

class Channel(Layer):
    def __init__(self, seed=None, **kwargs):
        super(self.__class__, self).__init__()

        self.positions = {}
        self.ip_id_mapping = {}

        # seed for packet error probability generation
        if seed:
            random.seed(seed)

        # read Friis parameters
        self.G = kwargs['G']  # antennas are symmetrical
        self.Pin = kwargs['Pin']
        self.lambda_ = kwargs['lambda_']

        # noise and time per bit
        self.No = kwargs['No']
        self.Ts = kwargs['Ts']  # symbol period

    def connect_upper_layer(self, upper_layer, **kwargs):
        super(self.__class__, self).connect_upper_layer(upper_layer, **kwargs)

        # store position and ip->id mapping
        self.positions[upper_layer.id_] = kwargs['position']
        self.ip_id_mapping[upper_layer.local_ip] = upper_layer.id_

    def compute_Pe_distance(self, upper_layer_id, dst_layer_id, packet_size):
        p1 = self.positions[upper_layer_id]
        p2 = self.positions[dst_layer_id]

        delta_x = p1[0] - p2[0]
        delta_y = p1[1] - p2[1]

        distance = sqrt(delta_x**2 + delta_y**2)

        # Friis formula: antenna are coordinated (no efficiency loss)
        Prx = self.G**2 * self.Pin * (self.lambda_ / (4 * pi * distance))**2

        # symbol are 0/1: 1 bit per symbol
        # use simple BPSK modulation
        Pb = 1/2 * erfc(sqrt(Prx * self.Ts / self.No))

        # suppose iid channel
        Pe = 1 - (1 - Pb) ** packet_size

        # check probabilities are indeed correct
        logging.log(logging.DEBUG,
                    "CHANNEL: Pe = {} for packet size {}"\
                    .format(Pe, packet_size))

        return Pe, distance

    def recv_from_up(self, packet, upper_layer_id):
        # we have IP layer (batman) just above channel
        dst_layer_id = self.ip_id_mapping[packet['dst_ip']]

        # compute packet error probability based on nodes distance
        Pe, distance = self.compute_Pe_distance(upper_layer_id,
                                                dst_layer_id,
                                                packet['size'])

        # evaluate the number of retransmissions required to deliver the packet
        n_retx = geometric(1 - Pe)

        # set processing time to 1ms
        round_trip_time = 2 * distance / c0 + 1e-3

        # schedule arrival at receiver
        event_queue.add(Event(action=lambda: self.send_up(packet, dst_upper_layer_id),
                              when=n_retx * round_trip_time + event_queue.now))

        logging.log(logging.DEBUG,
                    "CHANNEL: Packet {} will be received successfully at time {}"\
                    .format(packet, rx_time))


class BatmanLayer(Layer):
    # position in array of theparameters
    NEIGH_PKT_SIZE = 0
    NEIGH_TX_TIME = 1
    NEIGH_NEXT_HOP = 2

    def __init__(self, local_ip):
        super(self.__class__, self).__init__()

        self.local_ip = local_ip
        # TODO add BATMAN parameters
        # probability of success of the transmission with ExOR algorithm
        # the value associated to each key is a list  (pkt ok, pkt received,
        #  next_hop_ip)
        self.neighbour_succ = {}
        # tables of all other neighbours
        self.glob_neigh_succ = {}
        # node table about all other neighbour
        self.oth_neigh_succ = {}
        # count of packet sent to ip, so that it will be balanced
        self.pkt_count = {}
        # send a neighbour discover
        self.neigh_disc = 0

    def recv_from_up(self, packet, upper_layer_id):
        # TODO do BATMAN stuff
        # header modifications are kept in a dictionary inside packet class
        # ex. pkt['next_hop_ip'] = 10
        if self.neigh_disc % 50 == 0:
            # discovery of the neighbours. If Join=0, then it's in no nw
            # Join != 0 is the nw ID to join
            if bool(self.oth_neigh_succ):  # check if there are elements
                pkt = Packet(size=1,
                             header={
                                 'src_ip': self.local_ip,
                                 'dst_ip': 0,
                                 'join': 1,
                                 'oth_table': False
                             })
            else:
                pkt = Packet(size=1,
                             header={
                                 'src_ip': self. local_ip,
                                 'dst_ip': 0,
                                 'join': 1,
                                 'oth_table': dict(self.glob_neigh_succ)
                             })
            self.send_down(pkt)
            self.update_neigh()

        self.neigh_disc += 1
        self.send_down(packet)

    def recv_from_down(self, packet, lower_layer_id):
        # TODO use packet['next_hop_ip'] to perform routing
        # (and distinguish between next hop and destination ip)
        if packet['dst_ip'] == self.local_ip: # handle packet for me
            # I already have a link. Let's see if this is the same I stored
            src = packet['src_ip']
            if packet['src_ip'] in self.neighbour_succ.keys():
                for i, element in enumerate(self.neighbour_succ[src]):
                    if next_hop == packet['prev_hop_ip']:
                        updated = []
                        # add this transmission time
                        updated[self.NEIGH_TX_TIME] = self.neighbour_succ[src][i][self.NEIGH_TX_TIME] + packet['rx_time'] -  packet['tx_time']
                        # keep the previous hop
                        updated[self.NEIGH_NEXT_HOP] = packet['prev_hop_ip']
                        # update size
                        updated[self.NEIGH_PKT_SIZE] = packet['size'] + \ self.neighbour_succ[src][i][self.NEIGH_PKT_SIZE]
                        self.neighbour_succ[src][i] = updated
                        # I've done everything I need, so send up the packet
                        # and return
                        self.send_up(packet)
                        return
                # If I got here, the block inside the if inside the for ways
                # never executed. I add the entry as it's a new link and return
                size = packet['size']
                time = packet['rx_time'] - packet['tx_time']
                self.neighbour_succ[src] = [[size, time, packet['prev_hop_ip']]]
                updated = [size, time, packet['prev_hop_ip']]
                self.neighbour_succ[src].append(updated)
                self.send_up(packet)
                return
            else:  # add first entry
                size = packet['size']
                time = packet['rx_time'] - packet['tx_time']
                self.neighbour_succ[src] = [[size, time, packet['prev_hop_ip']]]
                self.send_up(packet)
                return

        elif packet['dst_ip'] == 0:       # node discovery
            if self.neighbour_succ['src_ip'] is None:
                # and packet['join'] == 1: ignored as we're not into groups
                self.neighbour_succ['src_ip'] = [0, 0, 0]
            if packet['oth_table'] is False:
                pass
            else:
                self.oth_neigh_succ[packet['src_ip']] = packet['oth_table']
                self.update_neigh()
                return
            # TODO TO CHECK
            # add source node to the list of surrounding nodes
            if not packet['src_ip'] in self.neighbour_succ:
                self.neighbour_succ[packet['src_ip']] = [
                    packet['size'],
                    packet['rx_time'] - packet['rx_time'],
                    packet['prev_hop_ip']
                ]
            # add also the direct neighbour
            if not packet['prev_hop_ip'] in self.neighbour_succ:
                self.neighbour_succ[packet['prev_hop_ip']] = [
                    packet['size'],
                    packet['rx_time'] - packet['rx_time'],
                    0
                ]

            # self.neighbour_succ[prev_hop][self.NEIGH_PKT_SIZE] += packet['size']
            # time = packet['rx_time'] - packet['tx_time']
            # self.neighbour_succ[prev_hop][self.NEIGH_TX_TIME] += time
            # # update global table
            # self.glob_neigh_succ[self.local_ip] = self.neighbour_succ
        # direct neighbour
        if self.neighbour_succ[packet['dst_ip']][self.NEIGH_NEXT_HOP] == 0:
            packet['next_hop_ip'] = packet['dst_ip']
        else:
            packet['next_hop_ip'] = self.find_next_hop(packet['dst_ip'])
            # self.neighbour_succ[packet['dst_ip']][2][0]

        packet['prev_hop_ip'] = self.local_ip
        self.send_down(packet)

        # if this node is destination, send to each one of the apps:
        # the application will take care of discarding packets not for it
        if packet['dst_ip'] == self.local_ip and packet['to_bat'] is True:
            # set as a direct neighbour and this is a protocol specific packet
            self.neighbour_succ[packet['src_ip']][2] = 0
        else:
            for layer_id in self.upper_layers_id:
                self.send_up(packet, layer_id)

    def connect_upper_layer(self, upper_layer, **kwargs):
        super(self.__class__, self).connect_upper_layer(upper_layer, **kwargs)

        # set local ip in application layer
        upper_layer.local_ip = self.local_ip

    def update_neigh(self):
        # Start w/ one node in the neighbour and look for the other way around
        allNodes = self.glob_neigh_succ.keys()
        temp_links = {}  # dict with nodes that don't have any pkt sent
        links_metric = []  # each node will have a metric
        # calculate link metrics
        for tmp_node_from in allNodes:
            for tmp_node_to in self.glob_neigh_succ[tmp_node_from]:
                rate = tmp_node_to[self.NEIGH_PKT_SIZE] / tmp_node_to[self.NEIGH_TX_TIME]
                via = tmp_node_to[self.NEIGH_NEXT_HOP]
                if via == 0:  # direct neighbour, so no calculation needed
                    pass
                if links_metric[(tmp_node_from, tmp_node_to)] is None:
                    if links_metric[(tmp_node_to, tmp_node_from)] is None:
                        # add the metric for the first time
                        links_metric[(tmp_node_to, tmp_node_from)] = (
                                1/rate, via)
                    else:  # it already exists with the opposite direction
                        prev_rate = links_metric[(tmp_node_to, tmp_node_from)][0]
                        prev_via = links_metric[(tmp_node_to, tmp_node_from)][1]
                        metric_ok = max(prev_rate, 1/rate)  # worst case
                        if metric_ok == prev_rate:  # choose the worst one
                            links_metric[(tmp_node_to, tmp_node_from)] = (
                            metric_ok, prev_via)
                        else:
                            links_metric[(tmp_node_to, tmp_node_from)] = (
                            metric_ok, via)
                else:  # direct approach
                    # choose the minimum of the rates
                    prev_rate = links_metric[(tmp_node_from, tmp_node_to)][0]
                    prev_via = links_metric[(tmp_node_from, tmp_node_to)][1]
                    metric_ok = max(prev_rate, 1/rate)  # worst case
                    if metric_ok == prev_rate:
                        links_metric[(tmp_node_from, tmp_node_to)] = (
                        metric_ok, prev_via)
                    else:
                        links_metric[(tmp_node_from, tmp_node_to)] = (
                        metric_ok, via)
        # done the metrics calculation. now I need to write the shortest path
        # TODO

    def find_next_hop(self, dst_ip):
        if len(self.neighbour_succ[dst_ip]) == 1:
            return self.neighbour_succ[dst_ip][self.NEIGH_NEXT_HOP]
        elif len(self.neighbour_succ[dst_ip]) == 0:
            return 0  # broadcast the message
        else:
            numEl = len(self.neighbour_succ[dst_ip])
            rand = random()
            for i in range(numEl):  # i look in which bucket the random fell
                if rand < (i+1)/numEl:  # I chose the neighbour in this bucket
                    return self.neighbour_succ[dst_ip][i][self.NEIGH_NEXT_HOP]


class ApplicationLayer(Layer):
    def __init__(self, interarrival_gen, size_gen, start_time, stop_time, local_port, local_ip=None):
        super(self.__class__, self).__init__()

        # save address details
        self.local_port = local_port

        # define the arrival process
        self.interarrival_gen = interarrival_gen
        self.size_gen = size_gen

        # set when packet generation has to stop
        self.stop_time = stop_time

        # count correctly received packets
        self.rx_packet_count = 0
        self.rx_packet_size = 0
        self.tx_packet_count = 0
        self.tx_packet_size = 0

        # end-to-end connection from src to dst ips
        # is handled here, for simplicity
        self.local_ip = local_ip

        # schedule start of transmissions
        event_queue.add(Event(action=lambda: self.generate_pkts(), when=start_time))

    def connect_app(self, other):
        # exchange local and remote ip address

        # note that IP is set when connecting to BATMAN layer
        self.dst_ip = other.local_ip
        other.dst_ip = self.local_ip

        self.dst_port = other.local_port
        other.dst_port = self.local_port

    @logthis(logging.INFO)
    def generate_pkts(self):
        size = next(self.size_gen)
        time_delta = next(self.interarrival_gen)
        next_gen_time = time_delta + event_queue.now

        if next_gen_time < self.stop_time:
            # send packet to lower layer
            p = Packet(size=size,
                       header = {
                           'src_ip':   self.local_ip,
                           'src_port': self.local_port,
                           'dst_ip':   self.dst_ip,
                           'dst_port': self.dst_port
                       })

            self.tx_packet_count += 1
            self.tx_packet_size += p.size
            self.send_down(p)

            # call function again after interarrival
            event_queue.add(Event(self.generate_pkts, when=next_gen_time))

    def recv_from_down(self, packet, lower_layer_id):
        if packet['dst_port'] == self.local_port and \
           packet['src_port'] == self.dst_port:

            # increment count if packet is for this layer
            self.rx_packet_count += 1
            self.rx_packet_size += packet.size
