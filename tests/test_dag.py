# -*- coding: utf-8 -*-
from math import exp, log

import numpy as np
import pytest

import DAG

def test_block():
    blk=Block(3,4,2)
    assert(blk.txs, 3)
    assert(blk.fathers_indices, 4)
    assert(blk.register, 2)
