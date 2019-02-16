import matplotlib
import matplotlib.pyplot as plt
# import numpy as np
import pandas as pd

font = {'family': 'normal',
        'size': 10}

matplotlib.rc('font', **font)

FIXED_PARAM = 'time'

data_original = pd.read_hdf("results/simulation_results_0_2019-02-16-14-26-33.hdf5")

app_rates = list(set(data_original['app_rate']))
node_nums = list(set(data_original['node_num']))

print(app_rates)
print(node_nums)
for node_num in node_nums:
    for app_rate in app_rates:
        print(node_num, app_rate)
        data = data_original[
            (data_original['node_num'] == node_num)
            & (data_original['app_rate'] == app_rate)
        ].groupby([FIXED_PARAM]).sum()

        data['selfish_num'] /= data['node_num']
        data['altruistic_num'] /= data['node_num']
        del data['s']
        # del data['selfish_num']
        # del data['altruistic_num']

        data = data.reset_index()

        # plot obj_func vs one of the parameters

        fig = plt.figure(figsize=(3.5, 3), frameon=False)
        ax = fig.gca()
        data.plot(ax=ax,
                  use_index=True,
                  x=FIXED_PARAM,
                  y=['altruistic_num', 'selfish_num'],
                  style='.',
                  title='N={}, app rate={:.2f}'.format(node_num, app_rate))

        ax.set(xlabel=FIXED_PARAM.replace('_', ' '),
               ylabel="Objective function")
        ax.set_xlim([60.0, 62.0])

        plt.tight_layout()
        # plt.show()
        plt.savefig("report/figures/obj_funcs/lovi-obj_func_vs_{}_N_{}_app_{}\
        .eps".format(FIXED_PARAM, node_num, app_rate))
