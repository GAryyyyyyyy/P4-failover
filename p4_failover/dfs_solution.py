import os
import sys
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../../utils/'))

from topo_lib import JsonTopo
from p4_failover_lib import *
from p4runtime_lib.switch import ShutdownAllSwitchConnections

def dfs_backup(topo, s, d):
    stack = [[("",s)]]
    visited = [s]
    while stack:
        cur_state = stack.pop()
        edge, node = cur_state[-1]
        adj_nodes = topo.adj[node]
        for cur_node in adj_nodes:
            if cur_node in visited:
                continue
            if cur_node == d:
                if node != s:
                    cur_state.append((topo[node][cur_node]['name'], cur_node))
                    return cur_state
                else:
                    continue    
            stack.append(cur_state)
            new_state = cur_state[:]
            new_state.append((topo[node][cur_node]['name'], cur_node))
            stack.append(new_state)
            break
    return [("", None)]

def calculate_backup_paths(topo):
    '''calculate backup path for each edge
    return a list.
    each list item is a dict {'switch':switch, 'port':port, 'backup_path':path}
    '''
    backup_path_list = []
    for link in topo.edges:
        backup_path = dfs_backup(topo, link[0], link[1])
        backup_path_list.append({'switch':link[0],'port':topo.nodes[link[0]][topo[link[0]][link[1]]['name']],'backup_path':backup_path})
        backup_path = dfs_backup(topo, link[1], link[0])
        backup_path_list.append({'switch':link[1],'port':topo.nodes[link[1]][topo[link[0]][link[1]]['name']],'backup_path':backup_path})
    return backup_path_list

def write_failover_config(p4info_helper, sw):
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.edge_to_port",
        match_fields={
            "meta.out_edge": (2)
        },
        action_name="MyIngress.recovery_forward",
        action_params={
            "port": 3,
        }
    )
    sw.WriteTableEntry(table_entry)
    print "Installed edge to port rule on %s" % sw.name

if __name__ == '__main__':
    #Step 1: construct topo using networkx
    topo_file = "topo/topology.json"
    jsonTopo = JsonTopo(topo_file)
    topo = jsonTopo.get_networkx_topo()

    #Step 2: calculate backup path using different algorithm e.g. dfs bfs and so on
    backup_paths = calculate_backup_paths(topo)
    print(backup_paths)

    #step 3: set up connection with each switch
    switches = {}
    p4info_file_path = './build/simple_recovery.p4.p4info.txt'
    bmv2_file_path = './build/simple_recovery.json'
    switches['s1'] = setup_connection(p4info_file_path, bmv2_file_path, 's1', '127.0.0.1:50051', 0)
    switches['s2'] = setup_connection(p4info_file_path, bmv2_file_path, 's2', '127.0.0.1:50052', 1)
    switches['s3'] = setup_connection(p4info_file_path, bmv2_file_path, 's3', '127.0.0.1:50053', 2)
    # switches['s1'] = 'helo'
    # switches['s2'] = 'helo'
    # switches['s3'] = 'helo'

    #step 4: push backup paths to each switch
    push_backup_paths_to_switches(p4info_file_path ,switches, backup_paths)
    
    #step 5: populate edge_to_port table
    populate_edge_to_port_table(p4info_file_path, switches, topo)

    #step 6: shut down connection with switch
    # switches['s1'].shutdown()
    # switches['s2'].shutdown()
    # switches['s3'].shutdown()

    # setup_connection('./build/simple_recovery.p4.p4info.txt', './build/simple_recovery.json')
    # ShutdownAllSwitchConnections()



    #     {
    #   "table": "MyIngress.port_backup_path",
    #   "match": {
    #     "standard_metadata.egress_spec": [2]
    #   },
    #   "action_name": "MyIngress.copy_path",
    #   "action_params": {
    #     "length": 2,
    #     "v1": 1,
    #     "v2": 2,
    #     "v3": 0,
    #     "v4": 0,
    #     "v5": 0,
    #     "v6": 0,
    #     "v7": 0,
    #     "v8": 0
    #   }
    # },

    # {
    #   "table": "MyIngress.edge_to_port",
    #   "match": {
    #     "meta.out_edge": [1]
    #   },
    #   "action_name": "MyIngress.recovery_forward",
    #   "action_params": {
    #     "port": 3
    #   }
    # }