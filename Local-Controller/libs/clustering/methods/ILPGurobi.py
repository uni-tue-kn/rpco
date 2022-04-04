from ortools.linear_solver import pywraplp

import gurobipy as gp
from gurobipy import GRB

from libs.Evaluator import Evaluator

from collections import defaultdict


class ILP:

    def __init__(self, samples=[], name="ILP", max_cluster_size=11, number_of_ports=32, mode=0):
        self.name = name
        self.samples = samples

        self.max_cluster_size = max_cluster_size

        self.unique_ports = list(range(1, number_of_ports + 1))

        self.solver = gp.Model("mip1")
        self.mode = mode

        self.solver.setParam('MIPGap', 0.03)
        self.solver.setParam('TimeLimit', 600)
        #self.solver.setParam("Heuristics", 0.5)

        self.variables = defaultdict(int)

    def get_variable(self, port=0, cluster=0):
        variable_name = "p" + str(port) + "-" + str(cluster)

        return self.variables.get(variable_name)

    def _exact_solution(self, n_clusters=1):
        """
        Exact (but probably bad modelled) solution
        Variable x represents packet copy per sample and cluster
        For each cluster in sample, calculate number of ports that use this cluster
            x <= ci_1 + ci-2 + ... +
        Futher, x needs to be larger than each binary variable in sum (so if one is 1, x is 1) & x <= 1 (exactly 1)
        :param n_clusters:
        :return:
        """
        # recirculation variables
        # x represents a single packet copy, we want as less packet copies as possible
        # x <= ci-1 + ci-2 + ci-3 + ... +
        # x >= ci_1
        # x >= ci_2
        # x >= ci_3
        # x <= 1
        # minimize over sum of x
        # number of recirculations
        recirc_variables = []
        i = 0
        for s in self.samples:
            # do we need cluster x?
            for n in range(n_clusters):
                i += 1
                v = self.solver.addVar(vtype=GRB.BINARY, name="recirc-" + str(i))
                recirc_variables.append(v)

                for port in s:
                    self.solver.addConstr(v >= self.get_variable(port=port, cluster=n), "recirc var " + str(port))

        formula = 0
        for rv in recirc_variables:
            formula += rv

        self.solver.setObjective(formula, GRB.MINIMIZE)


    def _exact_solution_4(self, n_clusters=1):
        """
        Exact (but probably bad modelled) solution
        Variable x represents packet copy per sample and cluster
        For each cluster in sample, calculate number of ports that use this cluster
            x <= ci_1 + ci-2 + ... +
        Futher, x needs to be larger than each binary variable in sum (so if one is 1, x is 1) & x <= 1 (exactly 1)
        :param n_clusters:
        :return:
        """
        # recirculation variables
        # x represents a single packet copy, we want as less packet copies as possible
        # x <= ci-1 + ci-2 + ci-3 + ... +
        # x >= ci_1
        # x >= ci_2
        # x >= ci_3
        # x <= 1
        # minimize over sum of x
        # number of recirculations
        recirc_variables = []
        i = 0
        for s in self.samples:
            # do we need cluster x?
            for n in range(n_clusters):
                i += 1
                v = self.solver.addVar(vtype=GRB.BINARY, name="recirc-" + str(i))
                recirc_variables.append(v)

                help_constraint = 0

                for port in s:
                    self.solver.addConstr(v >= self.get_variable(port=port, cluster=n), "recirc var " + str(port))
                    help_constraint += self.get_variable(port=port, cluster=n)

                self.solver.addConstr(v <= help_constraint)

        formula = 0
        for rv in recirc_variables:
            formula += rv

        self.solver.setObjective(formula, GRB.MINIMIZE)

    def _exact_solution_2(self, n_clusters=1):
        """
        Exact (but probably bad modelled) solution
        Variable x represents packet copy per sample and cluster
        For each cluster in sample, calculate number of ports that use this cluster
            x <= ci_1 + ci-2 + ... +
        Futher, x needs to be larger than each binary variable in sum (so if one is 1, x is 1) & x <= 1 (exactly 1)
        :param n_clusters:
        :return:
        """
        # recirculation variables
        # x represents a single packet copy, we want as less packet copies as possible
        # x <= ci-1 + ci-2 + ci-3 + ... +
        # x >= ci_1
        # x >= ci_2
        # x >= ci_3
        # x <= 1
        # minimize over sum of x
        # number of recirculations
        formula = 0
        recirc_variables = []
        formula = 0
        i = 0
        for s in self.samples:
            for n in range(n_clusters):
                i += 1
                tmp = []
                for port in s:
                    tmp.append(self.get_variable(port=port, cluster=n))
                r = self.solver.addVar(vtype=GRB.BINARY, name="recirc-" + str(i))
                recirc_variables.append(r)
                self.solver.addGenConstrMax(r, tmp)

        for rv in recirc_variables:
            formula += rv

        self.solver.setObjective(formula, GRB.MINIMIZE)

    def _exact_solution_3(self, n_clusters=1):
        """
        Exact (but probably bad modelled) solution
        Variable x represents packet copy per sample and cluster
        For each cluster in sample, calculate number of ports that use this cluster
            x <= ci_1 + ci-2 + ... +
        Futher, x needs to be larger than each binary variable in sum (so if one is 1, x is 1) & x <= 1 (exactly 1)
        :param n_clusters:
        :return:
        """
        # recirculation variables
        # x represents a single packet copy, we want as less packet copies as possible
        # x <= ci-1 + ci-2 + ci-3 + ... +
        # x >= ci_1
        # x >= ci_2
        # x >= ci_3
        # x <= 1
        # minimize over sum of x
        # number of recirculations
        recirc_variables = []
        i = 0

        for s in self.samples:
            # do we need cluster x?
            for n in range(n_clusters):
                i += 1
                v = self.solver.addVar(vtype=GRB.BINARY, name="recirc-" + str(i))
                recirc_variables.append(v)

                self.solver.addGenConstrOr(v, [self.get_variable(port=p, cluster=n) for p in s])


        formula = 0
        for rv in recirc_variables:
            formula += rv

        self.solver.setObjective(formula, GRB.MINIMIZE)

    def _approx_solution(self, n_clusters=1):
        """
        Idea: Maximize number of packets per sample that are in one cluster
        Use: Sqare of sum of packets per cluster --> better to have large cluster than small clusters per sample
        :param n_clusters:
        :return:
        """
        formula = 0

        for s in self.samples:
            for n in range(n_clusters):
                tmp = 0
                for port in s:
                    tmp += self.get_variable(port=port, cluster=n)
                formula += tmp * tmp

        self.solver.setObjective(formula, GRB.MAXIMIZE)

    def cluster(self, n_cluster=1):
        """
        Create binary variable per cluster-port combination, indicating if port is part of cluster
        E.g. p1-0 is 1, if port 1 is in cluster 0
        Ensure, that each port is associated with exactly one port
        Minimize recirculations with custom objective based on samples
        :param n_cluster:
        :return:
        """
        for n in range(n_cluster):
            for j in self.unique_ports:
                i = self.solver.addVar(vtype=GRB.BINARY, name="p" + str(j) + "-" + str(n))
                self.variables["p" + str(j) + "-" + str(n)] = i

        # add constraint that each port has to bee assigned to exactly one cluster
        for i in self.unique_ports:
            c1 = 0
            for j in range(n_cluster):
                c1 += self.get_variable(port=i, cluster=j)

            # exactly one cluster per port
            self.solver.addConstr(c1 == 1, str(c1) + " == 1")

        # max cluster size
        for n in range(n_cluster):
            s = 0
            for p in self.unique_ports:
                s += self.get_variable(port=p, cluster=n)

            self.solver.addConstr(s <= self.max_cluster_size, "cluster_size " + str(n))

        if self.mode == 0:
            self._approx_solution(n_clusters=n_cluster)

        if self.mode == 1:
            self._exact_solution(n_clusters=n_cluster)

        if self.mode == 2:
            self._exact_solution_2(n_clusters=n_cluster)

        if self.mode == 3:
            self._exact_solution_3(n_clusters=n_cluster)

        if self.mode == 4:
            self._exact_solution_4(n_clusters=n_cluster)

        self.solver.optimize()

        labels = {}

        for n in range(n_cluster):
            for i in self.unique_ports:
                if self.get_variable(port=i, cluster=n).x == 1:
                    labels[i] = n

        labels = dict(sorted(labels.items()))

        return labels

# samples = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
# ilp = ILP(samples=samples, max_cluster_size=3, number_of_ports=9, mode=3)
#
# labels = ilp.cluster(n_cluster=3)
#
# c_eval = Evaluator(labels=labels, samples=samples)
#
# print(labels)
# print(c_eval.get_recirculations())
