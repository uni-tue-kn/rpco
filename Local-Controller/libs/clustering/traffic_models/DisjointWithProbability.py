from libs.clustering.traffic_models.ParentModel import ParentModel

import random
import numpy as np


class DisjointWithProbability(ParentModel):

    def __init__(self, number_of_ports=32, group_sizes=[], name="", probability=1.0):
        super(DisjointWithProbability, self).__init__(number_of_ports=number_of_ports, name=name)

        self.all_ports = list(range(1, number_of_ports+1))

        # defines sizes of groups
        self._group_sizes = group_sizes

        self._groups = []

        self._assign_groups()

        self.probability = probability

    def get_groups(self):
        return self._groups

    def _assign_groups(self):
        for value in self._group_sizes:
            ports = random.sample(self._ports, value)
            self._groups.append(ports)

            self._ports = set(self._ports) - set(ports)

    def sample(self, n=1, mode=0, ports_per_sample=0):
        """
        We sample 'number_of_ports' bits/ports
        With prob. probability inside selected group, with 1-probability outside of group
        If we get a duplicate, we sample again
        :param n:
        :return:
        """
        samples = []
        for _ in range(n):
            group = list(random.choice(self._groups))
            other_ports = list(set(self.all_ports) - set(group))

            if mode == 0:
                binom_p = 1
                number_of_ports = np.random.binomial(n=int(ports_per_sample/binom_p), p=binom_p, size=1)[0]
            elif mode == 1:
                number_of_ports = random.randint(1, len(group))
            else:
                raise Exception("Mode not known: {}".format(mode))

            sample = []
            for _ in range(number_of_ports):
                sample_found = False

                while not sample_found:
                    perc = random.randint(0, 100)

                    # we sampled all packets from "main" group
                    if len(group) < 1:
                        # but we can still sample from "outside" group
                        if len(other_ports) >= 1:
                            s = random.sample(other_ports, k=1)[0]
                            other_ports.remove(s)
                            sample_found = True
                        else:
                            # there is no port left (number_of_ports seems to be very high)
                            s = []
                            sample_found = True
                    else:
                        # we can still sample "regularly"
                        if perc <= self.probability * 100:
                            s = random.sample(group, k=1)[0]
                            group.remove(s)
                            sample_found = True
                        elif len(other_ports) > 1:
                            # we have to sample outside of group, and there are still ports
                            s = random.sample(other_ports, k=1)[0]
                            other_ports.remove(s)
                            sample_found = True

                sample.append(s)

            if len(sample) != number_of_ports:
                raise Exception("Sample {} does not contain {} ports".format(s), number_of_ports)

            samples.append(sample)

        return samples


#m = DisjointWithProbability(number_of_ports=32, group_sizes=[11, 11, 10], name="DisjointWith Probability",
#                            probability=0.8)
#a = m.sample(10)

#print(m.get_groups())

#print(a)
