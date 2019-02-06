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
    def __init__(self, p_retx, rtt, dest_id=None):
        super(self.__class__, self).__init__()

        self.p_retx = p_retx
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
        tx_time = geometric(self.p_retx) * self.rtt
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
    def __init__(self, ip, neigh_disc_interval):
        super(self.__class__, self).__init__()

        ## single hop connection (via channels)
        self.destination_table = {
            # dest IP: ID of channel layer, populated via `connect_to`
        }

        ## routing address of node
        assert ip > 0, "Invalid reserved address {}".format(ip)
        self.ip = ip

        self.neigh_disc_interval = neigh_disc_interval

        # TODO add BATMAN parameters probability of success of the transmission
        # with ExOR algorithm the value associated to each key is a list
        # (pkt ok, pkt received, next_hop_ip)
        self.neighbour_succ = {}

        # tables of all other neighbours
        self.glob_neigh_succ = {}

        # count of packet sent to ip, so that it will be balanced
        self.pkt_count = {}

        # send a neighbour discover
        self.neigh_disc = 0

    def connect_to(self, other, **kwargs):
        """ Connect self with other node through Channel objects """

        # create two symmetric channels for the two directions
        c1 = Channel(**kwargs, dest_id=other.id_)
        self.destination_table[other.ip] = c1.id_

        c2 = Channel(**kwargs, dest_id=self.id_)
        other.destination_table[self.ip] = c2.id_

    def recv_from_up(self, packet, upper_layer_id):
        ## perform discrovery, if it is time to do so
        if self.neigh_disc % self.neigh_disc_interval == 0:
            # discovery of the neighbours. If Join=0, then it's in no nw
            # Join != 0 is the nw ID to join
            if bool(self.oth_neigh_succ): #check if there are elements
                pkt = Packet(size=1,
                             header={
                                 'src_ip': self.ip,
                                 'dst_ip': 0,
                                 'join': 1,
                                 'oth_table': False
                             })
            else:
                pkt = Packet(size=1,
                             header={
                                 'src_ip': self.ip,
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

        assert packet['next_hop_ip'] in self.destination_table, "Invalid next hop"
        self.send_down(packet,
                       lower_layer_id=self.destination_table[packet['next_hop_ip']])

    def recv_from_down(self, packet, lower_layer_id):
        # TODO use packet['next_hop_ip'] to perform routing
        # (and distinguish between next hop and destination ip)
        if packet['dst_ip'] != self.ip:
            # node discovery
            if packet['dst_ip'] == 0:
                if neighbour_succ['src_ip'] is None and packet['join'] == 1:
                    neighbour_succ['src_ip'] = [0,0,0]
                if packet['oth_table'] is False:
                    pass
                else:
                    self.oth_neigh_succ[packet['src_ip']] = packet['oth_table']
            # update the statistics to keep the nw stable
        else:
            prev_hop = packet['prev_hop_ip']

            if packet['is_ok']:
                # add source node to the list of surrounding nodes
                if not packet['src_ip'] in neighbour_succ:
                    self.neighbour_succ[packet['src_ip']] =[
                        packet['size'],
                        packet['size'],
                        prev_hop
                    ]
                self.neighbour_succ[prev_hop][0] += packet['size']
                self.neighbour_succ[prev_hop][1] += packet['size']

                # update global table
                self.glob_neigh_succ[self.ip] = self.neighbour_succ
            else:
                self.neighbour_succ[prev_hop][1] += packet['size']

            # direct neighbour
            if self.neighbour_succ[dst_ip][2] == 0:
                packet['next_hop_ip'] = packet['dst_ip']
            else:
                # select first for now
                packet['next_hop_ip'] = self.neighbour_succ[dst_ip][2][0]

            packet['prev_hop_ip'] = self.ip
            self.send_down(packet)

        # if this node is destination, send to each one of the apps:
        # the application will take care of discarding packets not for it
        if packet['dst_ip'] == self.ip and packet['to_bat'] is True:
            # set as a direct neighbour and this is a protocol specific packet
            self.neighbour_succ[packet['src_ip']][2] = 0
        else:
            for layer_id in self.upper_layers_id:
                self.send_up(packet, layer_id)

    def update_neigh():
        pass

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
        # exchange local and remote ip addresses

        # note that IP is set when connecting to BATMAN layer
        self.dst_ip = other.ip
        other.dst_ip = self.ip

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
