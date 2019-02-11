import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

font = {'family' : 'normal',
        'size'   : 10}

matplotlib.rc('font', **font)

FIXED_PARAM = 'selfish_rate'

data = pd.read_hdf("results/simulation_results.hdf5")

data = data[
    (data['node_num'] == 100) &
    (data['app_rate'] == data['app_rate'][1])
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
oth = input("suffix for file, no space allowed")
plt.savefig('report/figures/PUNISHobj_func_vs_{}_oth.eps'.format(FIXED_PARAM, oth))
