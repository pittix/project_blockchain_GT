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
    def connect_lower_layer(self, lower_layer):
        # this function always connects lower layers
        # to upper layers, by convention
        self.lower_layers_id.append(lower_layer.id_)

        # add self layer id_ to lower layer (connect both ways)
        lower_layer.upper_layers_id.append(self.id_)

    @logthis(logging.DEBUG)
    def recv_from_up(self, packet, upper_layer_id):
        raise NotImplemented

    @logthis(logging.DEBUG)
    def recv_from_down(self, packet, lower_layer_id):
        raise NotImplemented

class Channel(Layer):
    def __init__(self, seed=None):
        super(self.__class__, self).__init__()

        self.positions = {}

        # seed for packet error probability generation
        if seed:
            random.seed(seed)

    def get_id_from_ip(self, dst_ip):
        for id_ in self.upper_layers_id:
            layer = Layer.all_layers[id_]

            if dst_ip == layer.local_ip:
                return layer.id_

        raise ValueError("Invalid IP {}: maybe layer not connected to channel?".format(dst_ip))

    def recv_from_up(self, packet, upper_layer_id):
        # physical location pertains to upper layer (lowest for each node)
        # position = Layer.all_layers[upper_layer_id].position

        # TODO compute packet error probability *based on position, ...*
        Pe = -1

        # if error does not happen
        if random() > Pe:
            logging.log(logging.INFO, "CHANNEL: Packet {} transmitted successfully".format(packet))

            # we have IP layer (batman) just above channel
            dest_upper_layer_id = self.get_id_from_ip(packet['dst_ip'])

            # check if it is a good idea to set one
            # network should be small enough to be negligible though
            propagation_time = 0.1

            def handle_packet():
                dst_layer = Layer.all_layers[dest_upper_layer_id]
                dst_layer.recv_from_down(packet, dest_upper_layer_id)

            # if tp=0, no event scheduling is needed
            event_queue.add(Event(handle_packet,
                                  when=propagation_time + event_queue.now))
        else:
            logging.log(logging.INFO, "CHANNEL: Packet {} lost".format(packet))

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
        sendDown(packet)

    def recv_from_down(packet, lower_layer_id):
        # TODO use packet['next_hop_ip'] to perform routing
        # (and distinguish between next hop and destination ip)

        # if this node is destination, send to each one of the apps:
        # the application will take care of discarding packets not for it
        if packet['dst_ip'] == local_ip:
            for layer_id in self.upper_layers_id:
                sendUp(packet, layer_id)

class ApplicationLayer(Layer):
    def __init__(self, interarrival_gen, size_gen, stop_time,
                 local_ip, local_port, remote_ip, remote_port):
        super(self.__class__, self).__init__()

        # save address details
        self.local_ip = local_ip
        self.local_port = local_port
        self.remote_ip = remote_ip
        self.remote_port = remote_port

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

    @logthis(logging.INFO)
    def generate_pkts(self):
        size = next(self.size_gen)
        time_delta = next(self.interarrival_gen)
        next_gen_time = time_delta + event_queue.now

        if next_gen_time < self.stop_time:
            # send packet to lower layer
            p = Packet(size=size,
                       header = {
                           'src_ip': self.local_ip,
                           'src_port': self.local_port,
                           'dst_ip': self.remote_ip,
                           'dst_port': self.remote_port
                       })

            self.tx_packet_count += 1
            self.tx_packet_size += p.size
            self.send_down(p)

            # call function again after interarrival
            event_queue.add(Event(self.generate_pkts, when=next_gen_time))

    def recv_from_down(self, packet, lower_layer_id):
        if packet['dst_ip'] == self.local_ip and \
           packet['dst_port'] == self.local_port and \
           packet['src_ip'] == self.remote_ip and \
           packet['src_port'] == self.remote_port:

            # increment count if packet is for this layer
            self.rx_packet_count += 1
            self.rx_packet_size += packet.size
