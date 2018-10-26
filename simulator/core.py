from functools import total_ordering
from inspect import signature


class Base:
    # create a nice representation of current object
    def __repr__(self):
        arguments = ", ".join(["{}: {!r}".format(key, value) \
                               for key, value in self.__dict__.items()])
        return "<{}({})>".format(self.__class__.__name__, arguments)

@total_ordering
class Event(Base):
    def __init__(self, action, when):
        # check that action doesn't take any arguments
        # this means all needed variables have been
        # captured at its creation
        if len(signature(action).parameters) != 0:
            raise ValueError(
                'Event: action should not take any parameters to be called'
            )

        self.action = action
        self.when = when

    def trigger(self):
        self.action()

    def __lt__(self, other):
        return self.when < other.when

    def __eq__(self, other):
        return self.when == other.when

class EventQueue(Base):
    def __init__(self):
        self.events = []
        self.now = 0

    def next(self):
        next_event = self.events.pop()
        now = next_event.when
        return next_event

    def add(self, event):
        # add but keep list ordered
        self.events.insert(event, 0)
        self.events.sort()

    def now(self):
        return 0

class Packet(Base):
    last_packet_id = 0

    def __init__(self, size, header={}):
        self.size = size
        self.header = header

        Packet.last_packet_id += 1
        self.id_ = Packet.last_packet_id