class ParentModel(object):

    def __init__(self, number_of_ports=32, name=""):
        self._number_of_ports = number_of_ports
        self._ports = list(range(1, number_of_ports + 1))
        self.name = name

    def sample(self, n=1):
        pass

    def __str__(self):
        return self.name
