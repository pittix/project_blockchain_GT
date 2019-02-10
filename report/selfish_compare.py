import ast
from pathlib import Path

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

    selfish_obj = data[data['selfish'] == 1].total_packet_size.mean()
    altruistic_obj = data[data['selfish'] == 0].total_packet_size.mean()

    serie['selfish'] = selfish_obj
    serie['altruistic'] = altruistic_obj

    combined_results.append(serie)

results = pd.DataFrame(combined_results)
results.to_csv('../results/aggreagate_results.csv', index=None)
