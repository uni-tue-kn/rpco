from libs.clustering.traffic_models.ParentModel import ParentModel

import random


class Disjoint(ParentModel):

    def __init__(self, number_of_ports=32, group_sizes=[], name=""):
        super(Disjoint, self).__init__(number_of_ports=number_of_ports, name=name)

        # defines sizes of groups
        self._group_sizes = group_sizes

        self._groups = []

        self._assign_groups()

    def _assign_groups(self):
        for value in self._group_sizes:
            ports = random.sample(self._ports, value)
            self._groups.append(ports)

            self._ports = set(self._ports) - set(ports)

    def sample(self, n=1):
        samples = []
        for _ in range(n):
            group = random.choice(self._groups)
            ports = random.sample(group, k=random.randint(1, len(group)))

            samples.append(ports)

        return samples




