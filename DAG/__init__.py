# -*- coding: utf-8 -*-

# automatically compile Cython files
import numpy as np
import pyximport

pyximport.install(setup_args={"include_dirs" : np.get_include()})
