import networkx as nx
import matplotlib.pyplot as plt
import itertools


class WeightedGraph(object):
    def __init__(self, samples=[]):
        self._samples = samples
        self._graph = nx.Graph()

        self._init_graph()
        self._update_graph()

    def _init_graph(self):
        for s in self._samples:
            self._graph.add_nodes_from(s)

        # add initial edges
        for e in itertools.combinations(self._graph.nodes, 2):
            self._graph.add_edge(e[0], e[1], weight=0)

    def _update_graph(self):
        for s in self._samples:
            for e in itertools.combinations(s, 2):
                # no edge from A to A
                if len(set(e)) == 1:
                    continue

                self._graph[e[0]][e[1]]['weight'] += 1

    def get_graph(self):
        return self._graph

    def get_adjaceny_matrix(self):
        return nx.adjacency_matrix(self._graph)

    def show_graph(self, labels=[]):
        color_map = []

        colors = ["red", "blue", "green"]

        for n in self._graph:
            color_map.append(colors[labels.get(n)])

        plt.figure(10, figsize=(10, 10))
        pos = nx.spring_layout(self._graph, seed=5)
        nx.draw_networkx(self._graph, pos, node_color=color_map)
        nx.draw_networkx_edge_labels(self._graph, pos,
                                     edge_labels=nx.get_edge_attributes(self._graph, 'weight'))
        plt.show()
