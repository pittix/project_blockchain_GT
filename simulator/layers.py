import logging
from math import sqrt
from random import random

from numpy.random import geometric
from scipy.constants import Boltzmann, pi
from scipy.special import erfc

from .core import *


class Layer(Base):
    # static class variables
    last_layer_id = 0
    all_layers = {}

    def __init__(self):
        # set unique id
        Layer.last_layer_id += 1
        self.id_ = Layer.last_layer_id

        # store in a dict all Layers created, in order to look them up by id
        Layer.all_layers[self.id_] = self

    @logthis(logging.INFO)
    def send_up(self, packet, upper_layer_id):
        # event is immediate, fire it now without passing through event queue
        upper_layer = Layer.all_layers[upper_layer_id]
        upper_layer.recv_from_down(packet, self.id_)

    @logthis(logging.INFO)
    def send_down(self, packet, lower_layer_id):
        # event is immediate, fire it now without passing through event queue
        lower_layer = Layer.all_layers[lower_layer_id]
        lower_layer.recv_from_up(packet, self.id_)

    def recv_from_up(self, packet, upper_layer_id):
        raise NotImplemented

    def recv_from_down(self, packet, lower_layer_id):
        raise NotImplemented

class Sink(Layer):
    @logthis(logging.INFO)
    def recv_from_up(self, packet, upper_layer_id):
        pass

    @logthis(logging.INFO)
    def recv_from_down(self, packet, lower_layer_id):
        pass

class Channel(Layer):
    def __init__(self, p_succ, rtt, dest_id=None):
        super(self.__class__, self).__init__()

        self.p_succ = p_succ
        self.rtt = rtt
        self.dest_id = dest_id

        self.queue = []

    def recv_from_up(self, packet, upper_layer_id):
        # add packet to the queue
        self.queue.append(packet)

        # if it is the first in the queue, schedule its reception at dest_id
        if len(self.queue) == 1:
            self.schedule_tx()

    def schedule_tx(self):
        """ Add the next transmission to the event queue """
        tx_time = geometric(self.p_succ) * self.rtt
        event_queue.add(Event(action=self.transmit,
                              when=event_queue.now + tx_time))

    def transmit(self):
        """ Transmit the next packet waiting """
        assert len(self.queue) > 0, 'Empty queue while tx in {}'.format(self)

        if self.dest_id is None:
            raise ValueError("Destination ID not set in {}".format(self))

        # send the packet to destination
        self.send_up(self.queue.pop(), upper_layer_id=self.dest_id)

        # schedule the next transmission, if queue is not empty
        if len(self.queue) > 0:
            self.schedule_tx()

class BatmanLayer(Layer):
    # position in array of theparameters
    NEIGH_PKT_SIZE = 0
    NEIGH_TX_TIME = 1
    NEIGH_NEXT_HOP = 2

    def __init__(self, local_ip):
        super(self.__class__, self).__init__()

        ## single hop connection to neighbour layers

        self.neighbour_table = {
            # dest IP: ID of channel layer
        }
        self.app_table = {
            # local port: ID of app_layer
        }

        ## routing address of node
        assert local_ip > 0, "Invalid reserved address {}".format(local_ip)
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

    def connect_to(self, other, **kwargs):
        """ Connect self with other node through Channel objects """

        # create two symmetric channels for the two directions
        c1 = Channel(**kwargs, dest_id=other.id_)
        self.neighbour_table[other.ip] = c1.id_

        c2 = Channel(**kwargs, dest_id=self.id_)
        other.neighbour_table[self.ip] = c2.id_

    def connect_app(self, app_layer):
        # save information about upper layer
        self.app_table[app_layer.local_port] = app_layer.id_

        # register self in application layer
        app_layer.lower_layer_id = b_layer.id_

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
                                 'src_ip': self.local_ip,
                                 'dst_ip': 0,
                                 'join': 1,
                                 'oth_table': dict(self.glob_neigh_succ)
                             })
            self.send_down(pkt)
            self.update_neigh()
        else:
            self.neigh_disc+=1

        ## set next_hop for packet correctly
        # TODO

        assert packet['next_hop_ip'] in self.neighbour_table, "Invalid next hop"
        self.send_down(packet,
                       self.neighbour_table[packet['next_hop_ip']])
        self.neigh_disc += 1

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
        # TODO set lower layer (channel) id
        self.send_down(packet)

        # if this node is destination, send to each one of the apps:
        # the application will take care of discarding packets not for it
        if packet['dst_ip'] == self.ip:
            assert packet['dst_port'] in self.app_table

            upper_layer_id = self.app_table[packet['dst_port']]
            self.send_up(packet, upper_layer_id)

    def update_neigh(self):
        # Start w/ one node in the neighbour and look for the other way around
        allNodes = self.glob_neigh_succ.keys()
        temp_links = {}  # dict with nodes that don't have any pkt sent
        links_metric = []  # each node will have a metric
        # calculate link metrics
        for tmp_node_from in allNodes:
            for tmp_node_to in self.glob_neigh_succ[tmp_node_from]
                rate = tmp_node_to[self.NEIGH_PKT_SIZE] /  tmp_node_to[self.NEIGH_TX_TIME]
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
                            links_metric[(tmp_node_from, tmp_node_to)] = (
                            metric_ok, prev_via)
                        else:
                            links_metric[(tmp_node_from, tmp_node_to)] = (
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
        #TODO

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
    def __init__(self, interarrival_gen, size_gen, start_time, stop_time,
                 local_port, local_ip, dst_port, dst_ip):

        super(self.__class__, self).__init__()

        # save address details
        self.local_port = local_port
        self.local_ip = local_ip

        self.dst_port = dst_port
        self.dst_ip = dst_ip

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

        # schedule start of transmissions
        event_queue.add(Event(action=lambda: self.generate_pkts(), when=start_time))

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
            self.send_down(p, lower_layer_id=self.lower_layer_id)

            # call function again after interarrival
            event_queue.add(Event(self.generate_pkts, when=next_gen_time))

    def recv_from_down(self, packet, lower_layer_id):
        if packet['dst_port'] == self.local_port and \
           packet['src_port'] == self.dst_port:

            # increment count if packet is for this layer
            self.rx_packet_count += 1
            self.rx_packet_size += packet.size
