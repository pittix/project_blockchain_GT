import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

G = nx.read_gml("../results/s-1_node_num-50_dim-1000.0_dist_lim-400.0_app_rate-0.2_selfish_rate-0.2_stop_time-1.0.gml")

pos = {
    node: np.array([properties['x'], properties['y']])
    for node, properties in G.nodes(data=True)
}

fig = plt.figure(frameon=False)
ax = fig.gca()

ax.set_title("Network graph")

nx.draw(G, pos=pos, ax=ax)
nx.draw_networkx_labels(G, pos=pos, ax=ax)

plt.tight_layout()

# plt.show()
plt.savefig('figures/example_graph.eps')
