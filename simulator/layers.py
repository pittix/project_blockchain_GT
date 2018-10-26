import logging
from random import random

from .core import *

event_queue = EventQueue()

class Layer(Base):
    # static class variable, to avoid setting the same id twice
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

    @logthis(logger.INFO)
    def send_up(self, packet, upper_layer_id=None):
        if len(self.upper_layers_id) == 0:
            raise ValueError("Layer {} has no upper layers!".format(self))

        # set first upper layer as default one
        if not upper_layer_id:
            upper_layer_id = self.upper_layers_id[0]

        # event is immediate, fire it now without passing through event queue
        upper_layer = Layer.all_layers[upper_layer_id]
        upper_layer.recv_from_down(packet, self.id_)

    @logthis(logger.INFO)
    def send_down(self, packet, lower_layer_id=None):
        if len(self.lower_layers_id) == 0:
            raise ValueError("Layer {} has no lower layers!".format(self))

        # set first lower layer as default one
        if not lower_layer_id:
            lower_layer_id = self.lower_layers_id[0]

        # event is immediate, fire it now without passing through event queue
        lower_layer = Layer.all_layers[lower_layer_id]
        lower_layer.recv_from_up(packet, self.id_)

    @logthis(logger.DEBUG)
    def connect_lower_layer(self, lower_layer_id):
        # this function always connects lower layers
        # to upper layers, by convention
        self.lower_layers_id.append(lower_layer_id)

        # add self layer id_ to lower layer (connect both ways)
        Layer.all_layers[lower_layer_id].upper_layers_id.append(self.id_)

    def recv_from_up(self, packet, upper_layer_id):
        raise NotImplemented

    def recv_from_down(self, packet, lower_layer_id):
        raise NotImplemented

class Channel(Layer):
    def __init__(self, seed=None):
        super(self.__class__, self).__init__()

        self.positions = {}

        # seed for packet error probability generation
        if seed:
            random.seed(seed)

    def recv_from_up(self, packet, upper_layer_id):
        # physical location pertains to upper layer (lowest for each node)
        position = Layer.all_layers[upper_layer_id].position

        # TODO compute packet error probability *based on position, ...*
        Pe = 0.5

        # if error does not happen
        if random() > Pe:
            # we have IP layer (batman) just above channel
            dest_upper_layer_id = packet.header['ip.dest']

            # check if it is a good idea to set one
            # network should be small enough to be negligible though
            propagation_time = 0.1

            def handle_packet():
                dst_layer = Layer.all_layers[dest_upper_layer_id]
                dst_layer.recv_from_down(packet, dest_upper_layer_id)

            # if tp=0, no event scheduling is needed
            event_queue.add(Event(handle_packet,
                                  when=propagation_time + event_queue.now))

class BatmanLayer(Layer):
    def __init__(self, ip, position=(0, 0)):
        super(self.__class__, self).__init__()

        self.position = position
        self.ip = self.ip

        # TODO add BATMAN parameters

    def recv_from_up(packet, lower_layer_id):
        # TODO do BATMAN stuff
        # header modifications are kept in a dictionary inside packet class
        # ex. pkt.header['ip.next_hop'] = 10
        sendDown(packet)

class ApplicationLayer(Layer):
    def __init__(self, interarrival_gen, size_gen, stop_time):
        super(ApplicationLayer, self).__init__()

        # define the arrival process
        self.interarrival_gen = interarrival_gen
        self.size_gen = size_gen

        # set when packet generation has to stop
        self.stop_time = stop_time

    def generate_pkts(self):
        size = next(self.size_gen)
        time_delta = next(self.interarrival_gen)
        next_gen_time = time_delta + event_queue.now

        if next_gen_time < self.stop_time:
            # send packet to lower layer
            p = Packet(size=size)
            self.send_down(p)

            # call function again after interarrival
            event_queue.add(Event(self.generate_pkts, when=next_gen_time))
