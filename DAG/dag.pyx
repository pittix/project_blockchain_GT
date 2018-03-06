# -*- coding: utf-8 -*-
import cython
import numpy as np

cimport numpy as np

# -*- coding: utf-8 -*-
import numpy as np
cimport numpy as np

cdef class Block:
    def __init__(self, txs, fathers_indices, register):
        self.txs = txs
        self.fathers_indices = fathers_indices
        self.register = register


cdef class Transaction:
    cdef long payer, recipient, amount

    def __init__(self, payer, recipient, amount):
        self.payer = payer
        self.recipient = recipient
        self.amount = amount

    def explode(self):
        return (self.payer, self.recipient, self.amount)


GENESIS = 0
cdef class DAG:
    cdef long[:] leaves
    cdef long[:] parents
    cdef long[:] parents_pointers

    def __init__(self):
        # user 0 creates genesis and gives money to himself
        genesis = Block([], [], {0: 1e9})
        self.blocks = [genesis]
        self.leaves.append(GENESIS) # genesis index in blocks
        self.parents.append(GENESIS) # beginning of genesis parents
        self.parents.append(GENESIS) # ending of genesis parents

    def add(self, new_block):
        new_block_index = len(self.blocks)

        for i in range(self.parents_pointers[new_block_index], self.parents_pointers[new_block_index+1]):
            parent = self.blocks[i]
            current_register = parent.register

            for tx in new_block.txs:
                payer, recipient, amount = tx.explode()
                current_register[payer] -= amount

            if sum(np.array(current_register.values()) < 0) > 0:
                print("Block {} inconsistent with parent {}".format(new_block, self.blocks[i]))
                return

        self.blocks.append(new_block)
        self.leaves.append(new_block_index)

        for parent_index in new_block.fathers_indices:
            self.parents.append(parent_index)

        self.parents_pointers.append(len(self.parents))

    def get_main_chain(self, block_index):
        main_chain = []

        while block_index != GENESIS:
            main_chain.append(block_index)
            block_index = self.parent_pointers[block_index]

        return main_chain

    def get_transactions(self, block_index, T):
        visited = np.zeros(len(self.blocks))

        if visited[block_index] == 1:
            return T
        visited[block_index] = 1
        for i in range(self.parents_pointers[block_index], self.parents_pointers[block_index + 1]):
            T = self.get_transactions(i, T)

        for tx in self.blocks[block_index].txs:
            if tx.payer in register.keys():
