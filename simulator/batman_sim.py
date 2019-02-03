import logging
import sys

from .core import *
from .layers import *

SEED=1
square_x=10
square_y=20
GAIN=5
NOISE=10^(-4)
P_IN=0 #what's this?
T_S=10^(-5)
LAMBDA_=0.1 #what's this lambda?

def nodeCreation(node_num):
    nodes=[]
    for i in range(node_num):
        arg=dict({
            'position': [random.rand()*square_x, random.rand()*square_y],
            'G': GAIN,
            'No': NOISE,
            'Pin': P_IN,
            'lambda_': LAMBDA_
        })
        nodes.append(Channel(seed=SEED,args))

    return nodes

if __name__=='main':
    queue = EventQueue()
    nodes = nodeCreation(sys.argv[1])
