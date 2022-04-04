from libs.core.Log import Log
from libs.core.Event import Event
from libs.TopologyManager import TopologyManager, DeviceNotFound
from libs.TableEntryManager import TableEntryManager, TableEntry
from libs.Configuration import Configuration
from collections import defaultdict
from ipaddress import IPv4Network

from libs.clustering.traffic_models.DisjointWithProbability import DisjointWithProbability
from libs.clustering.traffic_models.Disjoint import Disjoint

from libs.controller.BierController import BierController
import networkx as nx

import random
from datetime import datetime

import numpy

random.seed(datetime.now())
#random.seed(10)

def flatten(t):
    return [item for sublist in t for item in sublist]

class IPv4Controller(object):
    """
    This module implements an IPv4 controller and sets the ipv4 forwarding entries
    including multicast forwarding entries
    """

    def __init__(self, base):
        """
        Init IPv4Controller with base controller and add IPv4 cli commands

        Args:
            base (libs.core.BaseController): Base controller object
        """
        self._baseController = base

        self.table_manager = TableEntryManager(controller=base, name="IPv4Controller")
        self.table_manager.init_table("ingress.ip_c.ip")
        self.table_manager.init_table("ingress.ip_c.encap_ipv4")

        self.static_rules()
        self.encap_model("s1")

    def encap_model(self, switch):
        n_ports = Configuration.get("model_params")["n_ports"]
        model = Configuration.get("model_params")["model"]

        if model == "Custom":
            p = Configuration.get("model_params")["p"]

            m = DisjointWithProbability(number_of_ports=n_ports, group_sizes=[5, 5, 5],
                                                name="DisjointWithProbability",
                                                probability=p)
            m._groups = [list(range(1, 13)), list(range(9, 17)), list(range(16, 20)), list(range(18, 24)), list(range(22, 30)), flatten([list(range(27, 33)), [1, 2, 3, 4]])]

            print(p)
        else:
            raise Exception("Unknown model")


        a = m.sample(n=2**14, mode=1)

        BierController.samples = a

        ts = [11, 12, 13, 15, 16, 17, 18, 19]
        #ts = [6, 3, 2]

        found = False
        for i in a:
            #print(sorted(i, reverse=True))
            if ts == sorted(i, reverse=True):
                found = True

        #if not found:
        #    print("sample not found!!!")



        def sample_to_bs(sample=None):
            bs = 0

            #sample = [3, 11, 18, 26]

            for s in sample:
                bfer = random.choice(BierController.get_port_to_bfers(s))
                bs |= 2**(bfer-1)

            return bs

        nh = []


        for index, sample in enumerate(a):
            nh.append(len(sample))

            if index % 1000 == 0: 
                Log.info(index)

            entry = TableEntry( match_fields={
                               "ig_md.random_header_index": index
                           },
                           action_name="ingress.ip_c.add_bier",
                           action_params={"bs": sample_to_bs(sample)}
                           )

            self._baseController.add_table_entry(table_name="ingress.ip_c.encap_ipv4", entry=entry)

            #TableEntryManager.handle_table_entry(self.table_manager,
            #                                     table_name="ingress.ip_c.encap_ipv4",
            #                                     table_entry=entry)


        Log.info("Write BitString model finished.")
        Log.info(numpy.mean(nh))

    def static_rules(self):
        entry = TableEntry( match_fields={
                               "hdr.ipv4.dst_addr": ("192.0.0.0", 8)
                           },
                           action_name="ingress.ip_c.forward",
                           action_params={"e_port": 132}
                           )

        TableEntryManager.handle_table_entry(self.table_manager,
                                             table_name="ingress.ip_c.ip",
                                             table_entry=entry)
