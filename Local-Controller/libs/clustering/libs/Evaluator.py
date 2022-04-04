import itertools

class Evaluator:

    def __init__(self, clusters=[], samples=[]):
        self.clusters = clusters
        #print(self.clusters)
        self.samples = samples

    def get_recirculations(self):
        recirculations = 0

        for s in self.samples:

            recirc = -1
            while len(s) > 0:
                clusters = sorted(self.clusters, key=lambda x: len(set(s) & set(x)), reverse=True)
                if len(clusters) > 0 and len(set(s) & set(clusters[0])) > 0:
                    s = set(s) - set(clusters[0])
                    recirc += 1
                else:
                    recirc += len(s)
                    break

            recirculations += recirc

        return recirculations

    def get_recirculations_per_sample(self):
        recirculations = 0

        for s in sorted(self.samples, key=lambda x: len(x), reverse=True):
            recirc = 0
            t = s
            if len(s) <= 1:
                continue
            while len(s) > 0:
                clusters = sorted(self.clusters, key=lambda x: len(set(s) & set(x)), reverse=True)
                if len(clusters) > 0 and len(set(s) & set(clusters[0])) > 0:
                    s = set(s) - set(clusters[0])
                    recirc += 1
                else:
                    recirc += len(s)
                    break

            #print(sorted(t, reverse=True), max(0, recirc-1))

            recirculations += max(0, recirc-1)

        #print(recirculations, float(recirculations) / len(self.samples))

        return float(recirculations) / len(self.samples)

    def get_recirculations_samples(self, samples=[]):
        recirculations = 0

        for s in samples:
            recirc = -1
            while len(s) > 0:
                for c in self.clusters:
                    if len(set(s) & set(c)) > 0:
                        s = set(s) - set(c)
                        recirc += 1

            recirculations += recirc

        return recirculations

    @staticmethod
    def get_entries(clusters=[]):
        return Evaluator.get_entries_3(clusters=clusters)

        cl = []

        all_entries = 0
        for c in clusters:
            # entries for this cluster
            entries = 2 ** len(c) - len(c) - 1 if len(c) > 1 else 0

            absorbed = []

            # look for overlaps with existing clusters
            for j in cl:
                t = set(c) & set(j)
                print("Absorbed:", absorbed)
                if len(t) > 1:
                    print("Remove {}".format(t))
                    # we already have this entries
                    entries -= 2 ** len(t) - len(t) - 1

                    absorbed.append(j)

            all_entries += max(0, entries)

            cl.append(c)

        return all_entries

    @staticmethod
    def get_entries_3(clusters=[]):
        return sum(map(lambda x: 2 ** len(x) - len(x) - 1 if len(x) > 1 else 0, clusters))

    @staticmethod
    def get_entries_2(clusters=[]):
        entries = []
        ret_entries = []

        for c in clusters:
            for i in range(2, len(c) +1):
                entries.append(list(itertools.combinations(c, i)))

        entries = [item for sublist in entries for item in sublist]

        for e in entries:
            t = list(e)
            t.sort()
            ret_entries.append(tuple(t))

        return len(set(ret_entries))

    def __str__(self):
        return "Recirculations per sample: {} with {} entries and clusters {}".format(self.get_recirculations_per_sample(), Evaluator.get_entries(clusters=self.clusters), self.clusters)
