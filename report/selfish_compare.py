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
variables = [
            "dim", "dist_lim", "node_num", "stop_time",
            "selfish_rate", "app_rate", "selfish", "altruistic"
            ]  # , 'selfish_num', 'altruistic_num', 'selfish', 'altruistic']
dim = [100, 200, 300, 400, 500, 600, 800, 1000]
dist_lim = 100
node_num = [10, 100]
stop_time = 100
selfish_rate = np.linspace(0.1, 0.7, num=20)
app_rate = np.linspace(0.01, 0.05, num=10)
analyzingData = pd.DataFrame(column=variables)
# average of the bitrate on seeds
for the_dim in dim:
    restricted_dim = results["dim"] == the_dim
    for the_node_num in node_num:
        restricted_node = results["node_num"] == the_node_num
        for the_selfish in selfish_rate:
            restricted_selfish = results["selfish_rate"] == the_selfish
            for the_app_rate in app_rate:
                restricted_app = results["app_rate"] == the_app_rate

                # sum over seeds and selfish
                data_to_sum = results[
                    restricted_dim & restricted_node & restricted_selfish
                    & restricted_app
                    ]
                # sum remaining columns
                total = data_to_sum.sum(axis=0)
                selfish = total['selfish']/total['selfish_num']
                altruistic = total['altruistic']/total['altruistic_num']
                # prepare new data to add
                to_analyze = {}
                to_analyze["dim"] = the_dim
                to_analyze["node_num"] = the_node_num
                to_analyze["selfish_rate"] = the_selfish
                to_analyze["app_rate"] = the_app_rate
                to_analyze["dist_lim"] = dist_lim
                to_analyze["stop_time"] = stop_time
                to_analyze["selfish"] = selfish
                to_analyze["altruistic"] = altruistic
                # add to the final analyzer
                analyzingData = analyzingData.append(to_analyze)

# save it
analyzingData.to_csv("averaged_simulations.csv")
