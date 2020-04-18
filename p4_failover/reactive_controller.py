import argparse
import sys
import socket
import random
import struct
import argparse

from scapy.all import sendp, send, get_if_list, get_if_hwaddr, hexdump
from scapy.all import Packet
from scapy.all import Ether, IP, UDP, TCP
from scapy.all import sniff, hexdump

import grpc
import os
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper

s1 = None
s3 = None
s4 = None
p4info_helper = None

def get_if():
    ifs=get_if_list()
    iface=None # "h1-eth0"
    for i in get_if_list():
        # if "eth0" in i:
        if "ens32" in i:
            iface=i
            break
    if not iface:
        print "Cannot find eth0 interface"
        exit(1)
    return iface

def send_pkt(iface, dst_ip_addr, message):
    addr = socket.gethostbyname(dst_ip_addr)

    print "sending on interface {} to IP addr {}".format(iface, str(addr))
    pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(dst=addr) / TCP(dport=1234, sport=random.randint(49152,65535)) / message
    pkt.show2()
    sendp(pkt, iface=iface, verbose=False)

def write_entry():
    global s1
    global s3
    global s4
    global p4info_helper
    
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.port_backup_path",
        match_fields={
            "standard_metadata.egress_spec": (2)
        },
        action_name="MyIngress.copy_path",
        action_params={
            "length": 2,
            "v1": 1,
            "v2": 2,
            "v3": 0,
            "v4": 0,
            "v5": 0,
            "v6": 0,
            "v7": 0,
            "v8": 0
        }
    )
    s1.WriteTableEntry(table_entry)
    
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.edge_to_port",
        match_fields={
            "meta.out_edge": (1)
        },
        action_name="MyIngress.recovery_forward",
        action_params={
            "port": 3
        }
    )
    s1.WriteTableEntry(table_entry)

    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.edge_to_port",
        match_fields={
            "meta.out_edge": (2)
        },
        action_name="MyIngress.recovery_forward",
        action_params={
            "port": 2
        }
    )
    s3.WriteTableEntry(table_entry)

    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.edge_to_port",
        match_fields={
            "meta.out_edge": (2)
        },
        action_name="MyIngress.recovery_forward",
        action_params={
            "port": 3
        }
    )
    s4.WriteTableEntry(table_entry)
    print "Table entry write success!"

def handle_pkt(pkt):
    print "Receive Pkt!"
    write_entry()
    sendp(pkt, iface=iface, verbose=False)


def main():
    p4info_file_path = './build/simple_recovery.p4.p4info.txt'
    global p4info_helper
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    
    global s1
    s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
            device_id=0,
    )
    s1.MasterArbitrationUpdate()
    
    # global s3
    # s3 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
    #         name='s3',
    #         address='127.0.0.1:50053',
    #         device_id=2,
    # )
    # s3.MasterArbitrationUpdate()
    # global s4
    # s4 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
    #         name='s4',
    #         address='127.0.0.1:50054',
    #         device_id=3,
    # )
    # s4.MasterArbitrationUpdate()

    iface = get_if()

    print "sniffing on %s" % iface
    sys.stdout.flush()
    sniff(iface = iface,
          prn = lambda x: handle_pkt(x))

    sleep(5)
    send_pkt(iface, "10.0.2.2", "hello")

    


if __name__ == '__main__':
    main()