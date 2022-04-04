import random
import math

from libs.clustering.libs.WeightedGraph import WeightedGraph


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


class RandomClustering:

    def __init__(self, name=""):
        self.name = name

    def cluster(self, samples=None, n_cluster=1, max_entries=1000000):
        graph = WeightedGraph(samples=samples)
        n_cluster = 1

        nodes = list(graph.get_graph().nodes)[:]
        random.shuffle(nodes)
        cluster = list(split(nodes, n_cluster))
        entries = sum(map(lambda x: 2 ** len(x) - 1 if len(x) > 1 else 0, cluster))

        while entries > max_entries:
            n_cluster += 1
            cluster = list(split(nodes, n_cluster))
            entries = sum(map(lambda x: 2 ** len(x) - 1 if len(x) > 1 else 0, cluster))

        if len(self.flatten(cluster)) != len(graph.get_graph().nodes):
            raise Exception("Not all nodes are in cluster")

        assigned = self.flatten(cluster)

        for node in graph.get_graph().nodes:
            if node not in assigned:
                cluster.append([node])

        return cluster

    def flatten(self, t):
        return [item for sublist in t for item in sublist]

    def _cluster_to_labels(self, cluster=[], graph=None):
        labels = {}

        for i, v in enumerate(cluster):
            for l in v:
                labels[l] = i

        assigned = self.flatten(cluster)
        c_id = len(cluster)

        for node in graph.get_graph().nodes:
            if node not in assigned:
                labels[node] = c_id
                c_id += 1

        return labels
