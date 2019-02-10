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
summary['selfish'] = summary['selfish'] / summary['selfish_num']
summary['altruistic'] = summary['altruistic'] / summary['altruistic_num']

# NaNs are generated when no selfish node was present: set the selfish bitrate
# to zero then
summary.fillna(0, inplace=True)

del summary['selfish_num']
del summary['altruistic_num']

summary.to_csv("results/averaged_simulations.csv")
