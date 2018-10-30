import logging
from random import randint, random

from simulator import *

logging.basicConfig(level=logging.DEBUG)

event_queue.clean()

channel = Channel()

def interarrival_gen():
    while True:
        yield random() * 10

def size_gen():
    while True:
        yield randint(100, 200)


app1 = ApplicationLayer(interarrival_gen(), size_gen(), stop_time=5000, local_port=1)
app2 = ApplicationLayer(interarrival_gen(), size_gen(), stop_time=5000, local_port=1)

# here should go
# b1 = BatmanLayer()
# b2 = BatmanLayer()
# b1.connect_upper_layer(app1)
# b2.connect_upper_layer(app2)

# now app1 and app2 have also IP addresses
app1.local_ip = 1
app2.local_ip = 2

channel.connect_upper_layer(app1, position=(0, 0))
channel.connect_upper_layer(app2, position=(1, 1))

app1.connect_app(app2)

event_queue.add(Event(action=lambda: app1.generate_pkts(), when=0))
# event_queue.add(Event(action=lambda: app2.generate_pkts(), when=0))
