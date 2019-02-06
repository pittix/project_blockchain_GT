import logging
from random import randint, random, randrange

from scipy.constants import Boltzmann, pi

from simulator import *

logging.basicConfig(level=logging.DEBUG)

# 1) load queue for events created in simulator module
event_queue.clean()

s = Sink()

c = Channel(0.5, 1)
c.dest_id = s.id_

p = Packet(size=1000, header = {})

for time in [1.0, 1.1, 1.2, 1.3]:
    event_queue.add(
        Event(action=lambda: c.recv_from_up(Packet(size=1000, header = {}), 0),
              when=time))

while True:
    next_event = event_queue.next()
    if next_event is None:
        break
