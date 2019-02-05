import logging
from random import randint, random, randrange

from scipy.constants import Boltzmann, pi

from simulator import *

logging.basicConfig(level=logging.DEBUG)

# 1) load queue for events created in simulator module
event_queue.clean()

# 2) create common channel
freq = 2.5e9 # ~ wifi is supposed
Temp = 293   # 20°C of noise temperature

channel = Channel(
    G=1.63,           # no dissipation is supposed in half-wave dipole, so gain = directivity
    Pin=10e-3,        # 10mW
    lambda_=c0/freq,
    Ts=2/freq,        # use Nyquist limit
    No=Boltzmann*Temp,
)

def create_node(ip, n_apps):
    # define interarrival and packet size for the app layer
    def interarrival_gen():
        while True:
            yield random() * 10

    def size_gen():
        while True:
            yield randint(100, 200)

    # create n app layers
    apps = [ ApplicationLayer(interarrival_gen(),
                              size_gen(),
                              start_time=0,
                              stop_time=5000,
                              local_port=n + 1) for n in range(n_apps) ]

    # create a single batman layer
    b = BatmanLayer(ip)

    # connect apps to batman layer
    for app in apps:
        b.connect_upper_layer(app)

    # connect the batman layer to the channel
    channel.connect_upper_layer(b, position=(random(), random()))

    return {
        'apps'  : apps,
        'batman': b
    }

# create n nodes with two apps each
n = 2
nodes = [create_node(i, 3) for i in range(n)]

for node in nodes:
    # connect each app to the corresponding one in a random node
    for i, app in enumerate(node['apps']):
        remote_app = nodes[randrange(n)]['apps'][i]
        app.connect_app(remote_app) # app now knows even remote IP

## run the simulation ##

while True:
    # trigger events until we run out of them
    if event_queue.next() is None:
        break
