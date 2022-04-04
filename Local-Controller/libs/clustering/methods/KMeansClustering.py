from sklearn.cluster import KMeans

from libs.WeightedGraph import WeightedGraph


class KMeansClustering(WeightedGraph):

    def __init__(self, samples=None, name=""):
        super().__init__(samples=samples)
        self.name = name
        self.samples = samples

    def cluster(self, n_cluster=1):
        clustering = KMeans(n_clusters=n_cluster,
                            random_state=0).fit(self.get_adjaceny_matrix())

        labels = {}

        for i, v in enumerate(self.get_graph().nodes):
            labels[v] = clustering.labels_[i]

        labels = dict(sorted(labels.items()))

        return labels

    def __str__(self):
        return self.name
