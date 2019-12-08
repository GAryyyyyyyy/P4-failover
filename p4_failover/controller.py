import os
import sys
from heapq import heappop, heappush
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '../utils/'))

from p4failover_lib.topo_lib import JsonTopo
from p4failover_lib.p4_failover_lib import *
from p4runtime_lib.switch import ShutdownAllSwitchConnections


def path_formater(topo, path):
    result = [('', path[0])]
    src_node = path[0]
    for i in range(1, len(path)):
        dst_node = path[i]
        result.append((topo[src_node][dst_node]['name'], dst_node))
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
                    heappush(q, (cost + 1, new_node, path))

    topo.add_edge(s, d, name=edge_name)

    if node == d:
        return path_formater(topo, path)
    return None


def dfs_backup(topo, s, d):
    stack = [[("", s)]]
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
    return None


def calculate_backup_configs(topo):
    '''calculate backup path for each edge
    return a list.
    each list item is a dict {'switch':switch, 'port':port, 'backup_path':path}
    '''
    backup_config_list = []
    for link in topo.edges:
        backup_path = dijkstra_backup(topo, link[0], link[1])
        backup_config_list.append({
            'switch':
            link[0],
            'port':
            topo.nodes[link[0]][topo[link[0]][link[1]]['name']],
            'backup_path':
            backup_path
        })
        backup_path = dijkstra_backup(topo, link[1], link[0])
        backup_config_list.append({
            'switch':
            link[1],
            'port':
            topo.nodes[link[1]][topo[link[0]][link[1]]['name']],
            'backup_path':
            backup_path
        })
    return backup_config_list


def recalculate_backup_path(topo, backup_configs):
    for backup_config in backup_configs:
        backup_path = backup_config['backup_path']
        if len(backup_path) == 1:
            src_sw, dst_sw = backup_path[0]
            new_backup_path = dijkstra_backup(topo, src_sw, dst_sw)
            if new_backup_path != None:
                print 'Backup path for %s to %s has been recovered!' % (src_sw,
                                                                        dst_sw)
                backup_config['backup_path'] = new_backup_path


def handle_link_up(sw1, sw2, topo, failing_edges, backup_configs):
    topo.add_edge(sw1, sw2, name=failing_edges.pop(sw1 + sw2))
    recalculate_backup_path(topo, backup_configs)


def handle_link_down(sw1, sw2, topo, failing_edges, backup_configs,
                     p4info_file_path, switches):
    down_edge_name = topo[sw1][sw2]["name"]
    failing_edges[sw1 + sw2] = down_edge_name
    topo.remove_edge(sw1, sw2)
    for backup_config in backup_configs:
        backup_path = backup_config['backup_path']
        if len(backup_path) == 1:
            continue  # the port does not have a backup path yet
        src_sw = backup_path[0][1]
        dst_sw = backup_path[-1][1]
        for edge_name, sw_name in backup_path:
            if edge_name == down_edge_name:
                #need to recalculate backup path
                new_backup_path = dijkstra_backup(topo, src_sw, dst_sw)
                if new_backup_path == None:
                    print 'Warnning! Cannot find backup path from %s to %s' % (
                        src_sw, dst_sw)
                    backup_config['backup_path'] = [(src_sw, dst_sw)]
                else:
                    backup_config['backup_path'] = new_backup_path
                    update_backup_config(p4info_file_path, switches,
                                         backup_config)
                    print 'Update new backup path for %s to %s: %s' % (
                        src_sw, dst_sw, str(new_backup_path))
                break


if __name__ == '__main__':
    #Step 1: construct topo using networkx
    topo_file = "topo/topology.json"
    jsonTopo = JsonTopo(topo_file)
    topo = jsonTopo.get_networkx_topo()

    #Step 2: calculate backup path using different algorithm e.g. dfs bfs and so on
    backup_configs = calculate_backup_configs(topo)
    print 'Initial back up paths:\n', backup_configs

    #step 3: set up connection with each switch
    switches = {}
    p4info_file_path = './build/simple_recovery.p4.p4info.txt'
    bmv2_file_path = './build/simple_recovery.json'
    switches['s1'] = setup_connection(p4info_file_path, bmv2_file_path, 's1', '127.0.0.1:50051', 0)
    switches['s2'] = setup_connection(p4info_file_path, bmv2_file_path, 's2', '127.0.0.1:50052', 1)
    switches['s3'] = setup_connection(p4info_file_path, bmv2_file_path, 's3', '127.0.0.1:50053', 2)
    # switches['s4'] = setup_connection(p4info_file_path, bmv2_file_path, 's4', '127.0.0.1:50054', 3)
    # switches['s5'] = setup_connection(p4info_file_path, bmv2_file_path, 's5', '127.0.0.1:50055', 4)
    # switches['s6'] = setup_connection(p4info_file_path, bmv2_file_path, 's6', '127.0.0.1:50056', 5)
    # switches['s7'] = setup_connection(p4info_file_path, bmv2_file_path, 's7', '127.0.0.1:50057', 6)
    # switches['s8'] = setup_connection(p4info_file_path, bmv2_file_path, 's8', '127.0.0.1:50058', 7)
    # switches['s9'] = setup_connection(p4info_file_path, bmv2_file_path, 's9', '127.0.0.1:50059', 8)
    # switches['s10'] = setup_connection(p4info_file_path, bmv2_file_path, 's10', '127.0.0.1:50060', 9)
    # switches['s11'] = setup_connection(p4info_file_path, bmv2_file_path, 's11', '127.0.0.1:50061', 10)
    # switches['s12'] = setup_connection(p4info_file_path, bmv2_file_path, 's12', '127.0.0.1:50062', 11)
    # switches['s13'] = setup_connection(p4info_file_path, bmv2_file_path, 's13', '127.0.0.1:50063', 12)
    # switches['s14'] = setup_connection(p4info_file_path, bmv2_file_path, 's14', '127.0.0.1:50064', 13)
    # switches['s15'] = setup_connection(p4info_file_path, bmv2_file_path, 's15', '127.0.0.1:50065', 14)
    # switches['s16'] = setup_connection(p4info_file_path, bmv2_file_path, 's16', '127.0.0.1:50066', 15)
    # switches['s17'] = setup_connection(p4info_file_path, bmv2_file_path, 's17', '127.0.0.1:50067', 16)
    # switches['s18'] = setup_connection(p4info_file_path, bmv2_file_path, 's18', '127.0.0.1:50068', 17)
    # switches['s19'] = setup_connection(p4info_file_path, bmv2_file_path, 's19', '127.0.0.1:50069', 18)
    # switches['s20'] = setup_connection(p4info_file_path, bmv2_file_path, 's20', '127.0.0.1:50070', 19)

    # #step 4: push backup paths to each switch
    push_backup_configs_to_switches(p4info_file_path ,switches, backup_configs)

    # #step 5: populate edge_to_port table
    populate_edge_to_port_table(p4info_file_path, switches, topo)

    print 'Initial configuration complete...'

    #tell controller which port is failed or has been repaired
    failing_edges = {}
    while True:
        config = raw_input("runtime_config> ")
        config = config.split()
        if len(config) != 3:
            print 'config should be: sw_name1 sw_name2 0/1 (0 for link down, 1 for link up)'
            continue
        if int(config[2]) == 0:
            handle_link_down(config[0], config[1], topo, failing_edges,
                             backup_configs, p4info_file_path, switches)
            print 'failing_edges: %s' % (str(failing_edges))
            print 'backup_configs: %s' % (str(backup_configs))
        else:
            handle_link_up(config[0], config[1], topo, failing_edges,
                           backup_configs)
            print 'failing_edges: %s' % (str(failing_edges))
            print 'backup_configs: %s' % (str(backup_configs))

    #step 6: shut down connection with switch
    #I am not sure are these necessary?---by house
    # ShutdownAllSwitchConnections()