import ast
from pathlib import Path

import numpy as np
import pandas as pd

results = pd.read_hdf("results/simulation_results.hdf5")

variables = list(results.columns)
for non_param in ('selfish_num', 'altruistic_num', 'selfish', 'altruistic'):
    variables.remove(non_param)

summary = results.groupby(variables).sum()

# element-by-element division

summary.to_csv("results/averaged_simulations.csv.gz")
