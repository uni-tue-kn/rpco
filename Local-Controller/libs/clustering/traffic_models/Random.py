from traffic_models.ParentModel import ParentModel

import random


class Random(ParentModel):

    def __init__(self, number_of_ports=32, name=""):
        super().__init__(number_of_ports=number_of_ports, name=name)

    def sample(self, n=1):
        samples = []
        for _ in range(n):
            ports = random.sample(list(range(1, self._number_of_ports+1)), k=random.randint(1, self._number_of_ports))

            samples.append(ports)

        return samples




