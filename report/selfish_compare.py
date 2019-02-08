import ast
from pathlib import Path

import pandas as pd

combined_results = []

for result_path in Path('../results').glob('*.csv'):
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
