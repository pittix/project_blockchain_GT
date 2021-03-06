import logging
from functools import total_ordering
# from inspect import signature
from types import FunctionType, GeneratorType

import networkx as nx


class Base:
    # create a nice representation of current object
    def __repr__(self):
        arguments = []

        for key, value in self.__dict__.items():
            if isinstance(value, FunctionType) or \
               isinstance(value, GeneratorType):
                arguments.append("key: {}".format(value.__name__))
            else:
                arguments.append("{}: {!r}".format(key, value))

        return "<{}({})>".format(self.__class__.__name__, ", ".join(arguments))


@total_ordering
class Event(Base):
    def __init__(self, action, when):
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
        # declare stop running out of events
        if len(self.events) == 0:
            return None

        next_event = self.events.pop()
        self.now = next_event.when

        next_event.trigger()

        return next_event

    def add(self, event):
        # add but keep list ordered
        self.events.append(event)
        self.events.sort(reverse=True)

    def clean(self):
        self.__init__()


class Packet(Base):
    last_packet_id = 0

    def __init__(self, size, header={}):
        self.size = size
        self.header = header

        Packet.last_packet_id += 1
        self.id_ = Packet.last_packet_id

    def __setitem__(self, key, item):
        self.header[key] = item

    def __getitem__(self, key):
        value = self.header[key]

        if value is None:
            raise ValueError("key = {} not in Packet {}".format(key, self))

        return value


def logthis(level):
    def _decorator(fn):
        def _decorated(*arg, **kwargs):
            logger.log(level,
                       "[%f] %s: args=%r, kwargs=%r",
                       event_queue.now,
                       fn.__name__,
                       arg,
                       kwargs)

            ret = fn(*arg, **kwargs)
            if ret:
                logger.log(level,
                           """\t called %s: args=%r,
                            kwargs=%r got return value: %r""",
                           fn.__name__,
                           arg,
                           kwargs,
                           ret)
            return ret
        return _decorated
    return _decorator


# create a logger for all interesting events
logger = logging.getLogger("simulator")

# create event queue
event_queue = EventQueue()

# graph containing the whole topology
G = nx.DiGraph()

DEFAULT_WEIGHT = 10
