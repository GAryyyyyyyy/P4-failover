# -*- coding: utf-8 -*-

import random
import time

import eval_topo
import dijkstra_base
import XPath_compression

def _edge_fail(topo, edge):
    dst_node = random.choice(list(topo.nodes))
    dijkstra_base.shortest_path_len_with_failure(topo, None, edge[1], dst_node)
    dijkstra_base.shortest_path_len_with_failure(topo, edge, edge[1], edge[0])
    dijkstra_base.shortest_path_len_with_failure(topo, edge, edge[1], dst_node)


def eval_avg_recovery_len(topo):
    # print len(topo.edges)
    total_len = 0 
    len_normal = 0
    len_failed = 0
    for edge in topo.edges:
        len_normal = dijkstra_base.avg_path_length_dijkstra(topo, edge[0])
        topo.remove_edge(edge[0], edge[1])
        len_failed = dijkstra_base.avg_path_length_dijkstra(topo, edge[0])
        total_len += (len_failed - len_normal)

        len_failed = dijkstra_base.avg_path_length_dijkstra(topo, edge[1])
        topo.add_edge(edge[0], edge[1])
        len_normal = dijkstra_base.avg_path_length_dijkstra(topo, edge[1])
        total_len += (len_failed - len_normal)
    
    # print total_len
    avg_len = total_len / len(topo.edges)
    print avg_len

    total_len = 0
    for edge in topo.edges:
        len_normal = 1
        len_failed = dijkstra_base.shortest_path_len_with_failure(topo, edge, edge[0], edge[1])
        total_len += (len_failed - len_normal)
        len_failed = dijkstra_base.shortest_path_len_with_failure(topo, edge, edge[1], edge[0])
        total_len += (len_failed - len_normal)

    avg_len = total_len / len(topo.edges)
    print avg_len

def path2XPath_path(topo, path):
    port = []
    for i in range(len(path)-1):
        port.append(topo.nodes[path[i]][path[i+1]])
    return [path, port]

def eval_memory_overhead(topo):
    # 计算无故障情况下，所有的path
    paths_normal = []
    for node in topo.nodes:
        paths_normal.extend(dijkstra_base.shortest_path_dijkstra(topo, node))
    # 为每一条path计算第一条边故障时的备份路径
    paths_failover = []
    for path in paths_normal:
        s = path[0]
        next_hop = path[1]
        d = path[-1]
        paths_failover.append(dijkstra_base.shortest_path_with_failure(topo, s, d, next_hop))

    # print len(paths_failover)

    entry_sum = 0
    paths_XPath = []
    for path in paths_failover:
        entry_sum += len(path) - 1
        paths_XPath.append(path2XPath_path(topo, path))

    print 'Naive 1:1 avg memory overhead:', float(entry_sum) / len(topo.nodes)
    # for h in paths_XPath:
    #     print h
    compression_result = XPath_compression.XPath_compression(paths_XPath)
    print 'XPath compression memory overhead:', compression_result

    port_sum = 0
    for node in topo.nodes:
        port_sum += len(topo.nodes[node])
    
    print 'Our solution memory overhead:', float(port_sum) / len(topo.nodes)

if __name__ == '__main__':
    print 'Topo: AB-fat-tree(8).'
    topo = eval_topo.AB_fat_tree_topo(8)
    eval_memory_overhead(topo)