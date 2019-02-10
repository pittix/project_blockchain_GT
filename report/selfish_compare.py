import ast
from pathlib import Path

import numpy as np
import pandas as pd

results = pd.read_hdf("../results/simulation_results.hdf5")

variables = list(results.columns)
for non_param in ('selfish_num', 'altruistic_num', 'selfish', 'altruistic'):
    variables.remove(non_param)

summary = results.groupby(variables).sum()

# element-by-element division
summary['selfish'] = summary['selfish'] / summary['selfish_num']
summary['altruistic'] = summary['selfish'] / summary['altruistic_num']

del summary['selfish_num']
del summary['altruistic_num']

summary.to_csv("averaged_simulations.csv")
