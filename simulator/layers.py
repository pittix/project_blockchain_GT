import logging
from math import pi, sqrt
from random import random

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
        self.Prx = kwargs['Prx']
        self.Gtx = kwargs['Gtx']
        self.Grx = kwargs['Grx']
        self.Pin = kwargs['Pin']
        self.lambda_ = kwargs['lambda_']

    def connect_upper_layer(self, upper_layer, **kwargs):
        super(self.__class__, self).connect_upper_layer(upper_layer, **kwargs)

        # store position and ip->id mapping
        self.positions[upper_layer.id_] = kwargs['position']
        self.ip_id_mapping[upper_layer.local_ip] = upper_layer.id_

    def compute_Pe(self, distance):
        # Friis formula
        self.Prx = self.Gtx * self.Grx * self.Pin * (self.lambda_ / (4 * pi * distance))**2

        # read modulation parameters and compute probability TODO
        Pe = 0

        return Pe

    def recv_from_up(self, packet, upper_layer_id):
        # physical location pertains to upper layer (lowest for each node)
        # position = Layer.all_layers[upper_layer_id].position

        dst_layer_id = self.ip_id_mapping[packet['dst_ip']]

        # compute distance between source and destination
        p1 = self.positions[upper_layer_id]
        p2 = self.positions[dst_layer_id]

        delta_x = p1.0 - p2.0
        delta_y = p1.1 - p2.1

        distance = sqrt(delta_x**2 + delta_y**2)

        # compute packet error probability based on nodes distance
        Pe = self.compute_Pe(distance)

        # if error does not happen
        if random() > Pe:
            # we have IP layer (batman) just above channel
            dst_upper_layer_id = self.ip_id_mapping[packet['dst_ip']]

            # check if it is a good idea to set one
            # network should be small enough to be negligible though
            c0 = 3e8
            propagation_time = distance / c0

            def handle_packet():
                self.send_up(packet, dst_upper_layer_id)

            rx_time = propagation_time + event_queue.now

            # if tp=0, no event scheduling is needed
            event_queue.add(Event(handle_packet, when=rx_time))

            logging.log(logging.DEBUG,
                        "CHANNEL: Packet {} will be received successfully at time {}"\
                        .format(packet, rx_time))

        else:
            logging.log(logging.DEBUG, "CHANNEL: Packet {} lost".format(packet))

class BatmanLayer(Layer):
    def __init__(self, local_ip, position=(0, 0)):
        super(self.__class__, self).__init__()

        self.position = position
        self.local_ip = local_ip
        # TODO add BATMAN parameters

    def recv_from_up(packet, upper_layer_id):
        # TODO do BATMAN stuff
        # header modifications are kept in a dictionary inside packet class
        # ex. pkt['next_hop_ip'] = 10
        send_down(packet)

    def recv_from_down(packet, lower_layer_id):
        # TODO use packet['next_hop_ip'] to perform routing
        # (and distinguish between next hop and destination ip)

        # if this node is destination, send to each one of the apps:
        # the application will take care of discarding packets not for it
        if packet['dst_ip'] == local_ip:
            for layer_id in self.upper_layers_id:
                send_up(packet, layer_id)

    def connect_upper_layer(self, upper_layer, **kwargs):
        super(self.__class__, self).connect_upper_layer(upper_layer, **kwargs)

        # set local ip in application layer
        upper_layer.local_ip = self.local_ip

class ApplicationLayer(Layer):
    def __init__(self, interarrival_gen, size_gen, stop_time, local_port, local_ip=None):
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
