from ortools.linear_solver import pywraplp

from collections import defaultdict

class ILP:

    def __init__(self, samples=[], name="ILP", max_cluster_size=11, number_of_ports=32):
        self.name = name
        self.samples = samples

        self.max_cluster_size = max_cluster_size

        self.unique_ports = list(range(1, number_of_ports+1))
        #print(self.unique_ports)

        self.solver = pywraplp.Solver.CreateSolver('SCIP')

        self.solver.set_time_limit(20000)


        self.infinity = self.solver.infinity()

    def cluster(self, n_cluster=1):
        port_variables = defaultdict(list)
        cluster_variables = defaultdict(list)
        variables = defaultdict(int)
        for n in range(n_cluster):
            for j in self.unique_ports:
                i = self.solver.IntVar(0.0, self.infinity, "p" + str(j) + "-" + str(n))
                port_variables[j].append(i)
                cluster_variables[n].append(i)
                variables["p" + str(j) + "-" + str(n)] = i

        # add constraint that each port has to bee assigned to exactly one cluster
        for i in self.unique_ports:
            c1 = 0
            for j in range(n_cluster):
                variable_name = "p" + str(i) + "-" + str(j)
                c1 += variables.get(variable_name)
                # positive
                self.solver.Add(variables.get(variable_name) >= 0)

            # exactly one cluster
            self.solver.Add(c1 == 1)


        # max cluster size
        for n in range(n_cluster):
            s = 0
            for v in cluster_variables.get(n):
                s+= v
            self.solver.Add(s <= self.max_cluster_size)

        # recirculation variables
        # x <= ci-1 + ci-2 + ci-3
        # x >= ci_1
        # x >= ci_2
        # x >= ci_3
        # number of recirculations
        formula = 0
        recirc_variables = []
        i = 0
        for s in self.samples:
            # do we need cluster x?
            for n in range(n_cluster):
                i += 1
                v = self.solver.IntVar(0.0, self.infinity, "recirc-" + str(i))
                recirc_variables.append(v)

                self.solver.Add(v <= 1)

                for port in s:
                    variable_name = "p" + str(port) + "-" + str(n)
                    self.solver.Add(v >= variables.get(variable_name))

        formula = 0
        for rv in recirc_variables:
            formula += rv

        #for s in self.samples:
        #    for port in s:
        #        variable_name = "p" +

        # balance clusters
        # product = 1
        # for n in range(n_cluster):
        #     cluster_size = 0
        #
        #     for port in cluster_variables.get(n):
        #         cluster_size += port
        #
        #     product += cluster_size

        #formula -= product

        print("Variables:", self.solver.NumVariables(), "Constraints:", self.solver.NumConstraints())


        self.solver.Minimize(formula)

        status = self.solver.Solve()

        #raise Exception('The problem does not have an optimal solution.')

        #print("Variables:", self.solver.NumVariables())
        #print("Constraints:", self.solver.NumConstraints())

        labels = defaultdict(list)

        for n in range(n_cluster):
            for i in self.unique_ports:
                variable_name = "p" + str(i) + "-" + str(n)
                #print(variable_name, variables.get(variable_name).solution_value())

                if variables.get(variable_name).solution_value() == 1:
                    labels[n].append(i)

        labels = dict(sorted(labels.items()))

        return labels



            #print(i, port_variables.get(i))


samples = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
ilp = ILP(samples=samples, max_cluster_size=3, number_of_ports=9)

print(ilp.cluster(n_cluster=3))