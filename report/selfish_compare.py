import ast
from pathlib import Path

import numpy as np
import pandas as pd

combined_results = []

for i, result_path in enumerate(Path('../results/csvs').glob('*.csv')):
    print("Done file {}".format(i), end='\r')
    serie = {}

    for unit in result_path.stem.split('-'):
        var, value = unit.split('=')

        # this parses int and float according to their string
        serie[var] = ast.literal_eval(value)

    data = pd.read_csv(result_path)
    # create a list with all values
    selfish_obj = data[data['selfish'] == 1].total_packet_size  # .mean()
    altruistic_obj = data[data['selfish'] == 0].total_packet_size  # .mean()

    # create only one mean, not mean of means
    serie['selfish_num'] = selfish_obj.count()
    serie['altruistic_num'] = altruistic_obj.count()
    serie['selfish'] = sum(selfish_obj)
    serie['altruistic'] = sum(altruistic_obj)
    combined_results.append(serie)

results = pd.DataFrame(combined_results)

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
