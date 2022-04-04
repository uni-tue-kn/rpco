from sklearn.cluster import SpectralClustering as SC

from libs.clustering.libs.WeightedGraph import WeightedGraph

from libs.clustering.libs.Evaluator import Evaluator

import math
import knapsack

from copy import deepcopy

import itertools
import time

import numpy as np
import networkx as nx
from scipy.sparse import csgraph
from collections import defaultdict



class RPCO:

    def __init__(self, name="", recursive=False, optimized_cluster_selection=False, overlap=False):
        self.name = name
        self.cur_entries = 0
        self.final_clusters = []
        self.recursive = recursive
        self.samples = []
        self.knapsack = optimized_cluster_selection
        self.graph = None
        self.overlap = overlap

    def cluster(self, samples=None, n_cluster=1, max_entries=1000000):
        self.samples = samples
        graph = WeightedGraph(samples=samples)
        self.graph = graph

        if n_cluster != -1:
            return self.overlap_cluster(graph=graph, cluster=self._cluster(graph=graph, n_cluster=n_cluster, max_entries=max_entries), max_entries=max_entries)

        return self._cluster_graph_auto(graph=graph, n_cluster=15, samples=samples, max_entries=max_entries)

    def overlap_cluster(self, graph=None, cluster=None, max_entries=1):
        entries = Evaluator.get_entries(clusters=cluster)

        if max_entries - entries > 0:
            nodes = self.flatten(cluster)
            nx_graph = graph.get_graph()

            node_cluster_count = []

            for c_id, c_val in enumerate(cluster):
                # is cluster "small" enough so that a new node can be added?
                entries = Evaluator.get_entries(clusters=cluster)
                cluster_lengths = map(lambda x: len(x), cluster)
                if (max_entries - entries - Evaluator.get_entries([c_val])) >= 2**min(cluster_lengths):
                    for node in [i for i in nodes if i not in c_val]:
                        count = sum(map(lambda x: nx_graph[node][x]['weight'], c_val))
                        node_cluster_count.append({"node": node, "cluster": c_id, "count": count})

            for x in [i for i in sorted(node_cluster_count, key=lambda x: x['count'], reverse=True) if i['count'] > 0]:
                temp_clusters = deepcopy(cluster)
                temp_clusters[x['cluster']].append(x['node'])

                if Evaluator.get_entries(temp_clusters) <= max_entries:

                    cluster[x['cluster']].append(x['node'])


        return cluster

    def _cluster_graph_auto(self, graph=None, n_cluster=1, samples=None, max_entries=1):
        clustering = []
        recirc = 10000

        for i in range(2, n_cluster+1):
            self.cur_entries = 0
            self.final_clusters = []

            cluster = self._cluster(n_cluster=i, graph=graph, max_entries=max_entries)

            if self.overlap:
                cluster = self.overlap_cluster(graph=graph, max_entries=max_entries, cluster=cluster)

            c_eval = Evaluator(clusters=cluster, samples=samples)

            rec = c_eval.get_recirculations_per_sample()

            if rec < recirc:
                clustering = cluster
                recirc = rec

            entries = Evaluator.get_entries(cluster)

            if entries > max_entries:
                raise Exception("Too much entries, allowed {}, got {}, with clusters: {}".format(max_entries, entries, cluster))

        return clustering

    def flatten(self, t):
        return [item for sublist in t for item in sublist]

    def _cluster(self, n_cluster=1, graph=None, max_entries=1000000):
        cluster = []
        labels = {}

        # there is only one node in the graph
        if len(graph.get_graph().nodes) > 2:
            clustering = SC(n_clusters=n_cluster,
                            assign_labels='discretize',
                            affinity='precomputed',
                            random_state=0).fit(graph.get_adjaceny_matrix())

            for i, v in enumerate(graph.get_graph().nodes):
                labels[v] = clustering.labels_[i]

            for i in range(n_cluster):
                cluster.append(list(filter(lambda x: labels[x] == i, labels)))
        else:
            cluster.append(graph.get_graph().nodes)

        # (weight, nodes)
        weighted_clusters = []

        if self.knapsack:
            weighted_clusters = self._knapsack_sort_cluster(cluster=cluster, graph=graph, max_entries=max_entries)
        else:
            weighted_clusters = self._weight_sort_cluster(cluster=cluster, graph=graph)

        for i in weighted_clusters:
            # we have still enough entries
            n_entries = Evaluator.get_entries(clusters=[i[1]])
            if self.cur_entries + n_entries <= max_entries or len(i[1]) == 1:
                if len(i[1]) != 1:
                    self.cur_entries += n_entries

                self.final_clusters.append(i[1])

            elif self.cur_entries < max_entries:
                if not self.recursive:
                    continue
                sub_graph = WeightedGraph()
                sub_graph._graph = graph.get_graph().subgraph(i[1])
                if max_entries - self.cur_entries > 2 ** 2:
                    number_of_cluster = 2
                    self._cluster(n_cluster=number_of_cluster, max_entries=max_entries, graph=sub_graph)

        return self.final_clusters

    def _cluster_link_count(self, graph=None, nodes=None):
        if nodes is None:
            nodes = []
        pairs = itertools.combinations(nodes, 2)

        weight = 0

        for p in pairs:
            weight += graph.get_edge_data(p[0], p[1]).get('weight')

        return weight

    def _knapsack_sort_cluster(self, cluster=[], graph=None, max_entries=1000000):
        size = []
        weight = []
        clusters = []
        ret = []

        baseline_recirc = Evaluator(clusters=[], samples=self.samples).get_recirculations_per_sample()

        for c in cluster:
            c_eval = Evaluator(clusters=[c], samples=self.samples)
            weight.append(baseline_recirc-c_eval.get_recirculations_per_sample())
            size.append(Evaluator.get_entries(clusters=[c]))
            clusters.append(c)

        selected = knapsack.knapsack(size, weight).solve(max_entries)

        for i, v in enumerate(clusters):
            if i in selected[1]:
                ret.append((10000, clusters[i]))
            else:
                c_eval = Evaluator(clusters=[v],
                                   samples=self.samples)
                ret.append((baseline_recirc-c_eval.get_recirculations_per_sample(), v))

        return sorted(ret, key=lambda x: x[0], reverse=True)

    def _weight_sort_cluster(self, cluster=[], graph=None):
        ret = []
        for v in cluster:
            ret.append((self._cluster_link_count(nodes=v, graph=graph.get_graph()), v))

        return sorted(ret, key=lambda x: x[0], reverse=True)
