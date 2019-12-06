import os
import sys
from heapq import heappop,heappush
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../utils/'))

from p4failover_lib.topo_lib import JsonTopo
from p4failover_lib.p4_failover_lib import *
from p4runtime_lib.switch import ShutdownAllSwitchConnections


def path_formater(topo, path):
    result = [('', path[0])]
    src_node = path[0]
    for i in range (1, len(path)):
        dst_node = path[i]
        result.append((topo[src_node][dst_node]['name'],dst_node))
        src_node = dst_node
    return result


def dijkstra_backup(topo, s, d):
    edge_name = topo[s][d]['name']
    topo.remove_edge(s, d)
    q = [(0, s, [])]
    visited = []
    while q:
        (cost, node, path) = heappop(q)
        if node not in visited:
            visited.append(node)
            path = path[:]
            path.append(node)
            if node == d:
                break
            for new_node in topo.adj[node]:
                if new_node not in visited:
                    heappush(q, (cost+1, new_node, path))

    topo.add_edge(s, d, name=edge_name)

    return path_formater(topo, path)


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
        backup_path = dijkstra_backup(topo, link[0], link[1])
        backup_path_list.append({'switch':link[0],'port':topo.nodes[link[0]][topo[link[0]][link[1]]['name']],'backup_path':backup_path})
        backup_path = dijkstra_backup(topo, link[1], link[0])
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
    topo_file = "fat_tree_topo/topology.json"
    jsonTopo = JsonTopo(topo_file)
    topo = jsonTopo.get_networkx_topo()

    #Step 2: calculate backup path using different algorithm e.g. dfs bfs and so on
    backup_paths = calculate_backup_paths(topo)
    print 'back up paths:\n', backup_paths

    #step 3: set up connection with each switch
    switches = {}
    p4info_file_path = './build/simple_recovery.p4.p4info.txt'
    bmv2_file_path = './build/simple_recovery.json'
    switches['s1'] = setup_connection(p4info_file_path, bmv2_file_path, 's1', '127.0.0.1:50051', 0)
    switches['s2'] = setup_connection(p4info_file_path, bmv2_file_path, 's2', '127.0.0.1:50052', 1)
    switches['s3'] = setup_connection(p4info_file_path, bmv2_file_path, 's3', '127.0.0.1:50053', 2)
    switches['s4'] = setup_connection(p4info_file_path, bmv2_file_path, 's4', '127.0.0.1:50054', 3)
    switches['s5'] = setup_connection(p4info_file_path, bmv2_file_path, 's5', '127.0.0.1:50055', 4)
    switches['s6'] = setup_connection(p4info_file_path, bmv2_file_path, 's6', '127.0.0.1:50056', 5)
    switches['s7'] = setup_connection(p4info_file_path, bmv2_file_path, 's7', '127.0.0.1:50057', 6)
    switches['s8'] = setup_connection(p4info_file_path, bmv2_file_path, 's8', '127.0.0.1:50058', 7)
    switches['s9'] = setup_connection(p4info_file_path, bmv2_file_path, 's9', '127.0.0.1:50059', 8)
    switches['s10'] = setup_connection(p4info_file_path, bmv2_file_path, 's10', '127.0.0.1:50060', 9)
    switches['s11'] = setup_connection(p4info_file_path, bmv2_file_path, 's11', '127.0.0.1:50061', 10)
    switches['s12'] = setup_connection(p4info_file_path, bmv2_file_path, 's12', '127.0.0.1:50062', 11)
    switches['s13'] = setup_connection(p4info_file_path, bmv2_file_path, 's13', '127.0.0.1:50063', 12)
    switches['s14'] = setup_connection(p4info_file_path, bmv2_file_path, 's14', '127.0.0.1:50064', 13)
    switches['s15'] = setup_connection(p4info_file_path, bmv2_file_path, 's15', '127.0.0.1:50065', 14)
    switches['s16'] = setup_connection(p4info_file_path, bmv2_file_path, 's16', '127.0.0.1:50066', 15)
    switches['s17'] = setup_connection(p4info_file_path, bmv2_file_path, 's17', '127.0.0.1:50067', 16)
    switches['s18'] = setup_connection(p4info_file_path, bmv2_file_path, 's18', '127.0.0.1:50068', 17)
    switches['s19'] = setup_connection(p4info_file_path, bmv2_file_path, 's19', '127.0.0.1:50069', 18)
    switches['s20'] = setup_connection(p4info_file_path, bmv2_file_path, 's20', '127.0.0.1:50070', 19)
    # switches['s1'] = 'helo'
    # switches['s2'] = 'helo'
    # switches['s3'] = 'helo'

    #step 4: push backup paths to each switch
    push_backup_paths_to_switches(p4info_file_path ,switches, backup_paths)
    
    #step 5: populate edge_to_port table
    populate_edge_to_port_table(p4info_file_path, switches, topo)

    #step 6: shut down connection with switch
    #I am not sure are these necessary?---by house
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