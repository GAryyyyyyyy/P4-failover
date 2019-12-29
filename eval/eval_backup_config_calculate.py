# -*- coding: utf-8 -*-

from heapq import heappop, heappush

# 这个文件是controller的完全拷贝，用于我们系统备份路径的计算，通过调用这个可以测试计算开销。

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
            topo.nodes[link[0]][link[1]],
            'backup_path':
            backup_path
        })
        backup_path = dijkstra_backup(topo, link[1], link[0])
        backup_config_list.append({
            'switch':
            link[1],
            'port':
            topo.nodes[link[1]][link[0]],
            'backup_path':
            backup_path
        })
    return backup_config_list