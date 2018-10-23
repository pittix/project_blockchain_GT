from functools import total_ordering


@total_ordering
class Event:
    def __init__(self, action, when):
        self.action = action
        self.when = when

    def trigger(self):
        self.action()

    def __lt__(self, other):
        return self.when < other.when

    def __eq__(self, other):
        return self.when == other.when

class EventQueue:
    def __init__(self):
        self.events = []

    def next(self):
        return self.events.pop()

    def add(self, event):
        # add but keep list ordered
        self.events.insert(event, 0)
        self.events.sort()
