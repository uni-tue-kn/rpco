#!/usr/bin/env python2

import argparse
import os
import sys
import threading
import time
from libs.core.BaseController import BaseController
from libs.controller.MacController import MacController
from libs.controller.IPv4Controller import IPv4Controller
from libs.controller.BierController import BierController
from libs.controller.MulticastController import MulticastController
from libs.core.Log import Log
from libs.MessageInHandler import MessageInHandler
from libs.core.Event import Event
from libs.Configuration import Configuration
from libs.TopologyManager import TopologyManager
from libs.TableEntryManager import TableEntry, TableEntryManager
from libs.PD import PDSetup
from scapy.all import *
import subprocess

def init_switches(controller=None, pd=None):
    """
    Connect to switches and set forwarding pipeline
    :param controller: base controller who handles connections
    :return:
    """
    controller.connect_and_arbitrate(grpc_port=Configuration.get('grpc_port'), device_id=Configuration.get('device_id'))
    controller.set_forwarding_pipeline_config()

    try:
        pd.setPorts(Configuration.get("ports"))
        pd.setMirrorSession(Configuration.get("ports"))
    except Exception as e:
        Log.error(e)

    Configuration.set('system_done', True)


def main():

    Event.activate()

    # base controller
    controller = BaseController(p4info_file_path=Configuration.get('p4info'), bmv2_path=Configuration.get('bmv2_json'),
                                prog_name=Configuration.get('prog_name'), bin_path=Configuration.get('bin_path'), cxt_json_path=Configuration.get('cxt_path'))


    # register event for new switch connections, this will add switches to device list
    Event.on('new_switch_connection', TopologyManager.add_device)

    # register events for static classes
    Event.on("packet_in", MessageInHandler.message_in)  # handles generic packet in

    # Create instances of sub controller
    mac = MacController(controller)

    pd = PDSetup()
    mc = MulticastController(pd=pd, base=controller)

    # start connection procedure
    init_switches(controller=controller, pd=pd)

    # BIER BFER to port mapping
    number_of_bfers = Configuration.get("model_params")["n_ports"]
    number_of_ports = Configuration.get("model_params")["n_ports"]


    for i in range(1, number_of_ports + 1):
        BierController.BFER_TO_PORT_MAPPING[i] = i




    ip = IPv4Controller(controller)
    bier = BierController(controller, mc)


    try:
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        pd.end()
	Log.info("Shutting down")
        os._exit(0)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')

    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='../P4-Implementation/build/sdn-bfr.p4info')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='../P4-Implementation/build/sdn-bfr.json')
    parser.add_argument('--grpc-port', help='GRPC port of switch',
                        type=int, action="store", required=True,
                        default=50051)
    parser.add_argument('--device-id', help='Device id of switch',
                        type=int, action="store", required=True,
                        default=1)
    parser.add_argument('--logfile', help='Name of the log file',
                        type=str, action="store", required=True,
                        default="log.txt")
    parser.add_argument('--loglevel', help='Log level',
                        type=int, action="store", required=False,
                        default=2)
    parser.add_argument('--prog-name', help='Name of programm',
                        type=str, action="store", required=True,
                        default="")
    parser.add_argument('--bin-path', help='Path of bin',
                        type=str, action="store", required=True,
                        default="")
    parser.add_argument('--cxt-path', help='Path of cxt',
                        type=str, action="store", required=True,
                        default="")
    parser.add_argument('--listen-port', help='Log level',
                        type=int, action="store", required=True,
                        default=30001)
    parser.add_argument('--bfr-id', help='Bfr id of switch',
                        type=int, action="store", required=True,
                        default=1)
    parser.add_argument('--ports', help='Name of the port file',
                        type=str, action="store", required=True,
                        default="tofino-ports.json")
    parser.add_argument('--config', help='path to config file',
                        type=str, action="store", required=True,
                        default='config.json')
    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print("\np4info file not found: %s\nHave you run 'make'?" % args.p4info)
        parser.exit(1)

    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print("\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json)
        parser.exit(1)

    # write all command line arguments to configuration
    Configuration.init(args)

    Log.log_file = Configuration.get('logfile')
    Log.log_level = Configuration.get('loglevel')

    try:
        main()
    except Exception as e:
        print(e)
        os._exit(1)
