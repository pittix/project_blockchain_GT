import logging
from functools import total_ordering
from inspect import signature
from types import FunctionType, GeneratorType

# speed of light [m/s]
c0 = 3e8

# create a logger for all interesting events
logger = logging.getLogger("")

def logthis(level):
    def _decorator(fn):
        def _decorated(*arg, **kwargs):
            logger.log(level,
                       "  calling %s: args=%r, kwargs=%r",
                       fn.__name__,
                       arg,
                       kwargs)

            ret = fn(*arg, **kwargs)
            if ret:
                logger.log(level,
                           "  called %s: args=%r, kwargs=%r got return value: %r",
                           fn.__name__,
                           arg,
                           kwargs,
                           ret)
            return ret
        return _decorated
    return _decorator

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
        # check that action doesn't take any arguments
        # this means all needed variables have been
        # captured at its creation
        # if len(signature(action).parameters) != 0:
            # print("----------------------> {}".format(signature(action)))
            # raise ValueError(
                # 'Event: action should not take any parameters to be called'
            # )

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
        self.now = next_event.when

        next_event.trigger()

        return next_event

    def add(self, event):
        # add but keep list ordered
        self.events.insert(0, event)
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
