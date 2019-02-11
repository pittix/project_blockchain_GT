import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

font = {'family' : 'normal',
        'size'   : 10}

matplotlib.rc('font', **font)

FIXED_PARAM = 'selfish_rate'

data = pd.read_csv("results/all_results_old.csv.gz")

data = data[
    (data['node_num'] == 100) &
    (data['app_rate'] == data['app_rate'][0])
].groupby([FIXED_PARAM]).sum()

data['selfish'] /= data['selfish_num']
data['altruistic'] /= data['altruistic_num']

del data['s']
del data['selfish_num']
del data['altruistic_num']

data = data.reset_index()

# plot obj_func vs one of the parameters

fig = plt.figure(figsize=(3.5, 3), frameon=False)
ax = fig.gca()

data.plot(ax=ax,
          use_index=True,
          x=FIXED_PARAM,
          y=['altruistic', 'selfish'],
          style='o-',
          title='Average node bitrate')

ax.set(xlabel=FIXED_PARAM.replace('_', ' ').capitalize(),
       ylabel="Objective function")

plt.tight_layout()
# plt.show()
plt.savefig('report/figures/obj_func_vs_{}.eps'.format(FIXED_PARAM))
