from traffic_models.ParentModel import ParentModel

import random


class NormalDistribution(ParentModel):

    # distribution config [(mean, std)]
    def __init__(self, number_of_ports=32, normal_distribution_config=[], name=""):
        super().__init__(number_of_ports=number_of_ports, name=name)

        self._distributions = []

        self._config = normal_distribution_config

        for i in normal_distribution_config:
            self._distributions.append(_Normal(min=1, mean=i[0], max=number_of_ports, std=i[1]))

    def sample(self, n=1):
        samples = []

        for _ in range(n):
            distribution = random.choice(self._distributions)
            num_ports = random.randint(1, 11)

            s = [distribution.sample() for _ in range(num_ports)]

            samples.append(list(set(s)))

        return samples

    def __str__(self):
        return self.name + "Config: " + str(self._config)


class _Normal:

    def __init__(self, mean=5, min=10, max=10, std=2):
        self.mean = mean
        self.min = min
        self.max = max
        self.std = std

    def sample(self):
        index = int(random.normalvariate(self.mean, self.std) + 0.5)

        if index < self.min:
            return self.min

        if index > self.max:
            return self.max

        return index
