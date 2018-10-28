import logging
from random import randint, random

from simulator import *

logging.basicConfig(level=logging.INFO)

event_queue.clean()

channel = Channel()

def interarrival_gen():
    while True:
        yield random() * 10

def size_gen():
    while True:
        yield randint(100, 200)

app1 = ApplicationLayer(interarrival_gen(), size_gen(), 5000, 1, 1, 2, 2)
app2 = ApplicationLayer(interarrival_gen(), size_gen(), 5000, 2, 2, 1, 1)

app1.connect_lower_layer(channel)
app2.connect_lower_layer(channel)

event_queue.add(Event(action=lambda: app1.generate_pkts(), when=0))
# event_queue.add(Event(action=lambda: app2.generate_pkts(), when=0))
