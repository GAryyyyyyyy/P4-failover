import time
import grpc
import os
import sys
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper

def write_entry_s1(p4info_helper, s1):
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

def write_entry_s3(p4info_helper, s3):
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

def write_entry_s4(p4info_helper, s4):
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


def main():
    start_time = time.time()
    p4info_file_path = '../p4_failover/build/simple_recovery.p4.p4info.txt'
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
            device_id=0,
    )
    s1.MasterArbitrationUpdate()
    s3 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s3',
            address='127.0.0.1:50053',
            device_id=2,
    )
    s3.MasterArbitrationUpdate()
    s4 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s4',
            address='127.0.0.1:50054',
            device_id=3,
    )
    s4.MasterArbitrationUpdate()
    write_entry_s1(p4info_helper, s1)
    write_entry_s3(p4info_helper, s3)
    write_entry_s4(p4info_helper, s4)
    time.sleep(2)
    end_time = time.time()
    print end_time - start_time

if __name__ == '__main__':
    main()