import logging
from random import randint, random, randrange

from simulator import *

logging.basicConfig(level=logging.DEBUG)

event_queue.clean()

freq = 2.5e9 # wifi is supposed
channel = Channel(
    G=1.63,     # no dissipation is supposed in half-wave dipole, so gain = directivity
    Pin=10e-3,    # 10mW
    lambda_=c0 / freq
)

def interarrival_gen():
    while True:
        yield random() * 10

def size_gen():
    while True:
        yield randint(100, 200)

def create_node(ip):
    app1 = ApplicationLayer(interarrival_gen(),
                            size_gen(),
                            start_time=0,
                            stop_time=5000,
                            local_port=1)

    app2 = ApplicationLayer(interarrival_gen(),
                            size_gen(),
                            start_time=4999,
                            stop_time=5000,
                            local_port=2)

    b = BatmanLayer(ip)
    b.connect_upper_layer(app1) # app1 now knows local IP
    b.connect_upper_layer(app2) # app2 now knows local IP

    channel.connect_upper_layer(b, position=(random(), random()))

    return {
        'apps' : [app1, app2],
        'batman': b
    }

# create n nodes with two apps each
n = 2
nodes = [create_node(i) for i in range(n)]

for node in nodes:
    # connect each app to the corresponding one in a random node
    for i, app in enumerate(node['apps']):
        remote_app = nodes[randrange(n)]['apps'][i]
        app.connect_app(remote_app) # app now knows even remote IP
