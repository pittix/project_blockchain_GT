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
    def __init__(self, p_succ, rtt, src_ip, dst_ip, dst_id):
        super(self.__class__, self).__init__()

        self.p_succ = p_succ
        self.rtt = rtt

        # record IP of source and destination, to identify the channel
        self.src_ip = src_ip
        self.dst_ip = dst_ip

        # register channel as edge in graph
        G.add_edge(src_ip, dst_ip)
        G[src_ip][dst_ip]['weight'] = DEFAULT_WEIGHT

        # id of destination
        self.dst_id = dst_id

        self.queue = []

        # record how much data have passed ~> bitrate
        self.tx_size = 0

    def recv_from_up(self, packet, upper_layer_id):
        # add packet to the queue
        self.queue.append(packet)

        # if it is the first in the queue, schedule its reception at dst_id
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

        pkt = self.queue.pop()

        # send the packet to destination
        self.send_up(pkt, upper_layer_id=self.dst_id)

        # update weight in graph with inverse of bitrate
        self.tx_size += pkt.size
        G[self.src_ip][self.dst_ip]['weight'] = event_queue.now / self.tx_size

        # schedule the next transmission, if queue is not empty
        if len(self.queue) > 0:
            self.schedule_tx()

class BatmanLayer(Layer):
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

        # register in graph
        G.add_node(local_ip)

    def connect_to(self, other, **kwargs):
        """ Connect self with other node through Channel objects """

        # create two symmetric channels for the two directions
        c1 = Channel(**kwargs, dst_id=other.id_)
        self.neighbour_table[other.local_ip] = c1.id_

        c2 = Channel(**kwargs, dst_id=self.id_)
        other.neighbour_table[self.local_ip] = c2.id_

        return {
            (self.local_ip, other.local_ip): c1,
            (other.local_ip, self.local_ip): c2
        }

    def connect_app(self, app_layer):
        # save information about upper layer
        self.app_table[app_layer.local_port] = app_layer.id_

        # register self in application layer
        app_layer.lower_layer_id = self.id_

    def recv_from_up(self, packet, upper_layer_id):
        path = ask_path(self.local_ip, packet['dst_ip'])
        packet['path'] = path
        self.send_down(packet,
                       self.neighbour_table[packet['path'][0]])

    def recv_from_down(self, packet, lower_layer_id):
        # TODO use packet['next_hop_ip'] to perform routing
        # (and distinguish between next hop and destination ip)
        if packet['path'][0] == self.local_ip: # handle packet for me
            assert packet['dst_port'] in self.app_table

            upper_layer_id = self.app_table[packet['dst_port']]
            self.send_up(packet, upper_layer_id)
        else:
            old_path = packet['path']
            new_path = old_path[1:]
            packet['path'] = new_path
            self.send_down(packet, packet['path'][0])

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
                           'dst_port': self.dst_port,
                           'tx_time': event_queue.now
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
