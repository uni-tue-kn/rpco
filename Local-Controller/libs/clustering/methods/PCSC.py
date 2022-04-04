from sklearn.cluster import SpectralClustering as SC

from libs.clustering.libs.WeightedGraph import WeightedGraph

from libs.clustering.libs.Evaluator import Evaluator

import math
import knapsack

import itertools
from collections import defaultdict


class PCSC:

    def __init__(self, name=""):
        self.name = name
        self.cur_entries = 0
        self.samples = []
        self.graph = None

    def cluster(self, samples=None, max_entries=1000000, n_cluster=1):
        self.samples = samples
        graph = WeightedGraph(samples=samples)
        self.graph = graph

        return self._cluster_graph_auto(graph=graph, max_entries=max_entries)

    def _cluster_graph(self, graph=None, n_cluster=1, max_entries=1):
        cluster = self._cluster(n_cluster=n_cluster, graph=graph)

        return cluster

    def _cluster_graph_auto(self, graph=None, max_entries=1):
        cluster = []
        for i in range(1, min(len(graph.get_graph().nodes.values())+1, 32+1)):
            cluster = self._cluster_graph(n_cluster=i, graph=graph)
            entries = sum(map(lambda x: 2**len(x) - 1 if len(x) > 1 else 0, cluster))

            if entries <= max_entries:
                break

        return cluster

    def get_labels(self, labels):
        ret = defaultdict(list)

        for i in labels:
            ret[labels[i]].append(i)

        return sorted(ret.items())

    def flatten(self, t):
        return [item for sublist in t for item in sublist]

    def _cluster(self, n_cluster=1, graph=None):
        cluster = []
        labels = {}

        if n_cluster == len(graph.get_graph().nodes()):
            for v in graph.get_graph().nodes:
                cluster.append([v])

            return cluster

        clustering = SC(n_clusters=n_cluster,
                        assign_labels='discretize',
                        affinity='precomputed',
                        random_state=0).fit(graph.get_adjaceny_matrix())

        for i, v in enumerate(graph.get_graph().nodes):
            labels[v] = clustering.labels_[i]

        for i in range(n_cluster):
            cluster.append(list(filter(lambda x: labels[x] == i, labels)))

        return cluster
