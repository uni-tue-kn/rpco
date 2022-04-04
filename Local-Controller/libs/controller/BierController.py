from libs.core.Log import Log
from libs.TableEntryManager import TableEntryManager, TableEntry
from libs.core.Event import Event
from libs.TopologyManager import TopologyManager
from libs.Configuration import Configuration

from time import sleep

from libs.clustering.traffic_models.DisjointWithProbability import DisjointWithProbability
from libs.clustering.methods.RPCO import RPCO
from libs.clustering.methods.PCSC import PCSC
from libs.clustering.methods.RandomClustering import RandomClustering

from libs.clustering.libs.Evaluator import Evaluator


from libs.packet_header.BIER import BIER

from collections import defaultdict
from itertools import chain, combinations

import math
import threading

class BierController(object):
    """
    This module implements an MacController and
    sets rewrite rules for layer 2
    """

    BFER_TO_PORT_MAPPING = {}

    samples = []

    @staticmethod
    def get_port_to_bfers(port):
        bfers = []

        for i in BierController.BFER_TO_PORT_MAPPING:
            if BierController.BFER_TO_PORT_MAPPING[i] == port:
                bfers.append(i)

        return bfers

    def __init__(self, base, mc):
        """
        Init BierController with base controller

        Args:
            base (libs.core.BaseController): Base controller
        """

        # table manager
        self.table_manager = TableEntryManager(controller=base, name="BierController")
        self.table_manager.init_table("ingress.bier_c.reset_clone")
        self.table_manager.init_table("ingress.bier_c.reset_clone_2")
        self.table_manager.init_table("ingress.bier_c.reset_clone_3")
        self.table_manager.init_table("ingress.bier_c.default_bift")
        self.table_manager.init_table("ingress.bier_c.bift")
        self.table_manager.init_table("ingress.bier_c.cluster")

        self.mc = mc

        entry = TableEntry(match_fields={"hdr.bier_md.bs": 0},
                                        action_name="ingress.bier_c.nop")

        TableEntryManager.handle_table_entry(manager=self.table_manager,
                                            table_name="ingress.bier_c.reset_clone",
                                            table_entry=entry)

        TableEntryManager.handle_table_entry(manager=self.table_manager,
                                            table_name="ingress.bier_c.reset_clone_2",
                                            table_entry=entry)

        TableEntryManager.handle_table_entry(manager=self.table_manager,
                                            table_name="ingress.bier_c.reset_clone_3",
                                            table_entry=entry)

        self.default_bift()



        Event.on("bier_pkt_in", self.bier_pkt_in)

        self.samples = []

        cluster = []

        for port in set(BierController.BFER_TO_PORT_MAPPING.values()):
            cluster.append([port])

        #cluster = [[23, 24, 25, 26, 27, 28, 29, 30, 17], [16, 17, 18, 19, 20, 21, 22, 24, 23, 25], [10, 11, 12, 13, 14, 15, 16, 19, 17], [1, 2, 3, 4, 5, 6, 7, 8, 9, 31, 32]]

        #self.build_cluster_selection(cluster=cluster)

        #eval = Evaluator(clusters=cluster, samples=BierController.samples)
        #print(eval)

        #self.model(labels=labels)

    def ports_to_bfers(self, ports = []):
        bfers = map(lambda x: BierController.get_port_to_bfers(x), ports)
        bfers = [i for j in bfers for i in j]

        #print(bfers)
        return sum(map(lambda x: 2**(x-1), bfers))

    def powerset(self, seq):
        if len(seq) <= 1:
            yield seq
            yield []
        else:
            for item in self.powerset(seq[1:]):
                yield [seq[0]] + item
                yield item

    def build_cluster_entries(self, cluster=[], valid_entries = []):
        comb = filter(lambda x: len(x) >= 1, [x for x in self.powerset(cluster)])
        cluster_id = self.cluster_to_id[str(cluster)]

        for i in sorted(comb, key = lambda x: len(x)):
            bs = self.ports_to_bfers(ports=i)
            #print(BierController.BFER_TO_PORT_MAPPING)
            inverted = 0xFFFFFFFFFFFFFFFFF ^ bs

            self.mc.update_mc_group(bs, i)

            entry = TableEntry(match_fields={"ig_md.temp_bs": (0, inverted), "ig_md.cluster_id": cluster_id},
                               action_name="ingress.bier_c.mc_forward",
                               action_params={"fbm": bs, "mgrp_id": self.mc.mcgrp_to_id[bs]},
                               priority=100-len(i)
                               )


            TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                 table_name="ingress.bier_c.bift",
                                                 table_entry=entry)

            valid_entries.append(entry.match_fields)

    def default_bift(self):
        # default bift
        all_bfers = BierController.BFER_TO_PORT_MAPPING.keys()
        #all_bfers = []

        for p in all_bfers:
            bs = 2**(p-1)

            # todo: add mapping from port to real tofino port
            port = BierController.BFER_TO_PORT_MAPPING[p]

            entry = TableEntry(match_fields={"hdr.bier.bs": (bs, bs)},
                               action_name="ingress.bier_c.forward",
                               action_params={"fbm": bs, "e_port": port},
                               priority=1
                            )




            TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                 table_name="ingress.bier_c.default_bift",
                                                 table_entry=entry)


    def build_cluster_selection(self, cluster=[]):
        self.cluster_to_id = {}

        for i, v in enumerate(cluster):
            self.cluster_to_id[str(v)] = i + 1

        valid_cluster_entries = []
        for c in cluster:
            self.build_cluster_entries(cluster=c, valid_entries=valid_cluster_entries)

        valid_entries = []
        comb = [x for x in self.powerset(filter(lambda x: len(x) > 1, cluster))]
        for i in sorted(comb, key = lambda x: len(x)):
            #continue
            if len(i) == 0:
                continue


            bs = 0
            for e in i:
                #print(self.ports_to_bfers(ports=e))
                bs |= self.ports_to_bfers(ports=e)


            inverted = 0xFFFFFFFFFFFF ^ bs
            cluster_id = self.cluster_to_id[str(i[0])]


   #         print("Combination {} with bs {} and invert {} id {}".format(i, bin(bs), bin(inverted), cluster_id))
   #         print("103 & Inverted = {}".format(bin(103 & inverted)))
            entry = TableEntry(match_fields={"hdr.bier.bs": (0, inverted)},
                               action_name="ingress.bier_c.set_cluster",
                               action_params={"fbm": self.ports_to_bfers(ports=i[0]), "cluster_id": cluster_id},
                               priority=100-len(i)
                               )


            TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                 table_name="ingress.bier_c.cluster",
                                                 table_entry=entry)

            valid_entries.append(entry.match_fields)



        # default bift
        all_bfers = BierController.BFER_TO_PORT_MAPPING.keys()
        #all_bfers = []

        for p in all_bfers:
            bs = 2**(p-1)

            # todo: add mapping from port to real tofino port
            port = BierController.BFER_TO_PORT_MAPPING[p]

            entry = TableEntry(match_fields={"hdr.bier.bs": (bs, bs)},
                               action_name="ingress.bier_c.set_cluster",
                               action_params={"fbm": bs, "cluster_id": 0},
                               priority=1
                               )

            inverted = 0xFFFFFFFFFFFFFFFFF ^ bs


            TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                 table_name="ingress.bier_c.cluster",
                                                 table_entry=entry)

            forward_entry = TableEntry(match_fields={"ig_md.cluster_id": 0, "ig_md.temp_bs": (0, inverted)},
                               action_name="ingress.bier_c.forward",
                               action_params={"fbm": bs, "e_port": port},
                               priority=1
                               )


            TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                 table_name="ingress.bier_c.cluster",
                                                 table_entry=entry)

            TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                 table_name="ingress.bier_c.bift",
                                                 table_entry=forward_entry)


            valid_entries.append(entry.match_fields)
            valid_cluster_entries.append(forward_entry.match_fields)

        Log.info("Finish cluster rules.")


        #self.table_manager.remove_invalid_entries(table_name="ingress.bier_c.cluster", valid_entries=valid_entries)
        #self.table_manager.remove_invalid_entries(table_name="ingress.bier_c.bift", valid_entries=valid_cluster_entries)



    def bier_pkt_in(self, packet=None):
        p = []

        b = packet[BIER].BitString

        for i in sorted(BierController.BFER_TO_PORT_MAPPING.keys(), reverse=True):
            if b >= 2**(i-1):
                b -= 2**(i-1)
                port = BierController.BFER_TO_PORT_MAPPING[i]
                p.append(port)

        #print("sample:", p)

        self.samples.append(p)

        if(len(self.samples) > 2**10):
            Event.off("bier_pkt_in", self.bier_pkt_in)
            Configuration.set("sample", False)
            Log.debug("Cluster...")

            if Configuration.get('cluster_type') == "RPCO":
                method = RPCO(name="RPCO", recursive=True,
                                    optimized_cluster_selection=True, overlap=True)
            elif Configuration.get('cluster_type') == "PCSC":
                method = PCSC(name="PCSC")
            else:
                method = RandomClustering(name="Random")

            cluster = method.cluster(samples=self.samples, n_cluster=-1, max_entries = Configuration.get("model_params")["max_entries"])

            #eval = Evaluator(clusters=cluster, samples=self.samples)
            #print(eval)

            #print("All samples")
            #eval = Evaluator(clusters=cluster, samples=BierController.samples)
            #print(eval)
            #cluster = [list(range(1, 9)), list(range(9, 17)), list(range(17, 25)), list(range(25, 33))]
            threading.Thread(target=self.build_cluster_selection, kwargs={"cluster": cluster}).start()



    def model(self, labels=[]):
        #m = DisjointWithProbability(number_of_ports=20, group_sizes=[7, 7, 6], name="DisjointWithProbability", probability=0.8)

        #a = m.sample(2**11)


        ports = []

        clusters = defaultdict(list)

        for l in labels:
            clusters[labels.get(l)].append(l)


        for c in clusters:
            p = clusters.get(c)
            out = sum([map(list, combinations(p, i)) for i in range(len(p) + 1)], [])


            out.remove([])

            ports.extend(out)


        def ports_to_bs(ports):
            ret = 0
            for p in ports:
                ret += 2**(p-1)

            return ret

        valid_entries = []


        for p in ports:
            bs = ports_to_bs(p)


            self.mc.update_mc_group(bs, p)


            entry = TableEntry(match_fields={"hdr.bier.bs": (bs, bs)},
                               action_name="ingress.bier_c.clone_and_forward",
                               action_params={"fbm": bs, "mgrp_id": self.mc.mcgrp_to_id[bs]},
                               priority=len(p)
                               )


            TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                 table_name="ingress.bier_c.bift",
                                                 table_entry=entry)


            valid_entries.append(entry.match_fields)

        self.table_manager.remove_invalid_entries(table_name="ingress.bier_c.bift", valid_entries=valid_entries)



        Log.debug("Model finished")
        Log.info(clusters)
