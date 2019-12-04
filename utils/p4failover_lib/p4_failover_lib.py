import grpc
import os
import sys
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../../utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper

#As if we do not need them
# def backup_path_to_bmv2_config(topo, path):
#     bmv2_config = []
#     edge,src_node = path[0]
#     for i in range(1,len(path)):
#         edge, dst_node = path[i]
#         bmv2_config.append((src_node, edge, topo.nodes[src_node][edge]))
#         src_node = dst_node
#     return bmv2_config

# def backup_paths_to_bmv2_configs(topo, paths):
#     bmv2_configs = []
#     for path in paths:
#         bmv2_config = backup_path_to_bmv2_config(topo, path)
#         bmv2_configs.append(bmv2_config)
#     return bmv2_configs

def _format_backup_path(backup_path):
    path = [0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(1, len(backup_path)):
        edge_name = backup_path[i][0]
        path[i-1] = int(edge_name[5:])
    return path

def push_backup_paths_to_switches(p4info_file_path, switches, backup_paths):
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    for backup_path in backup_paths:
        switch_name, port, path = backup_path['switch'], backup_path['port'], backup_path['backup_path']
        if len(backup_path) > 8:
            print("Back up path length cannot exceed 8")
            continue
        sw = switches[switch_name]
        formated_path = _format_backup_path(path)
        table_entry = p4info_helper.buildTableEntry(
            table_name="MyIngress.port_backup_path",
            match_fields={
                "standard_metadata.egress_spec": (port)
            },
            action_name="MyIngress.copy_path",
            action_params={
                "length": len(path) - 1,
                "v1": formated_path[0],
                "v2": formated_path[1],
                "v3": formated_path[2],
                "v4": formated_path[3],
                "v5": formated_path[4],
                "v6": formated_path[5],
                "v7": formated_path[6],
                "v8": formated_path[7],
            }
        )
        sw.WriteTableEntry(table_entry)

def setup_connection(p4info_file_path, bmv2_file_path, name, address, device_id):
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    try:
        s = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name=name,
            address=address,
            device_id=device_id,
            )
        # Send master arbitration update message to establish this controller as
        # master (required by P4Runtime before performing any other write operation)
        # s1.MasterArbitrationUpdate()
        s.MasterArbitrationUpdate()
        return s

    except KeyboardInterrupt:
        print " Shutting down."
    except grpc.RpcError as e:
        printGrpcError(e)

def populate_edge_to_port_table(p4info_file_path, switches, topo):
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    for node in topo.nodes:
        sw = switches[node]
        for edge_name in topo.nodes[node]:
            port = topo.nodes[node][edge_name]
            edge = int(edge_name[5:])
            table_entry = p4info_helper.buildTableEntry(
                table_name="MyIngress.edge_to_port",
                match_fields={
                    "meta.out_edge": (edge)
                },
                action_name="MyIngress.recovery_forward",
                action_params={
                    "port": port,
                }
            )
            sw.WriteTableEntry(table_entry)