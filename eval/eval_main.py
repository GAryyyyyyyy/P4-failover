# -*- coding: utf-8 -*-

import random
import time

import eval_topo
import dijkstra_base
import XPath_compression


def _path2XPath_path(topo, path):
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
        paths_XPath.append(_path2XPath_path(topo, path))

    print 'Naive 1:1 avg memory overhead:', float(entry_sum) / len(topo.nodes)
    # for h in paths_XPath:
    #     print h
    compression_result = XPath_compression.XPath_compression(paths_XPath)
    print 'XPath compression memory overhead:', compression_result

    port_sum = 0
    for node in topo.nodes:
        port_sum += len(topo.nodes[node])
    
    print 'Our solution memory overhead:', float(port_sum) / len(topo.nodes)


def eval_recovery_path_length_overhead(topo, sample_sum = 100):
    paths_origin = []
    for node in topo.nodes:
        paths_origin.extend(dijkstra_base.shortest_path_dijkstra(topo, node))
    
    path_overhead_sum_optimal = 0
    path_overhead_sum_our_solution = 0
    sample_count = 0
    while sample_count < sample_sum:
        selected_path = random.choice(paths_origin)
        # 利用dijkstra算出第一跳故障后的最优（最短）恢复路径
        path_length_origin = len(selected_path)
        path_length_failover = len(dijkstra_base.shortest_path_with_failure(topo, selected_path[0], selected_path[-1], selected_path[1]))
        if path_length_failover == 0: #说明这个点无法进行故障恢复，直接跳过了
            continue
        path_overhead_sum_optimal += ( path_length_failover - path_length_origin )
    
        # 使用我们的port-based恢复方法，计算路径开销
        path_overhead_our_solution = len(dijkstra_base.port_based_recovery_path_dijkstra(topo, selected_path[0], selected_path[1])) -1 - 1
        path_overhead_sum_our_solution += path_overhead_our_solution
        sample_count += 1

    print 'Optimal avg path length overhead: {} hops/fail'.format( float(path_overhead_sum_optimal) / sample_sum )
    print 'Our solution avg path length overhead: {} hops/fail'.format( float(path_overhead_sum_our_solution) / sample_sum )
        

if __name__ == '__main__':
    topo = eval_topo.topology_zoo_topo('./topology_zoo_topo/BtAsiaPac.gml')
    # topo = eval_topo.AB_fat_tree_topo(8)
    print 'Topo:', topo.name
    print '# of switches:', len(topo.nodes)
    print '# of links:', len(topo.edges)
    # eval_memory_overhead(topo)
    # eval_avg_recovery_len(topo)
    eval_recovery_path_length_overhead(topo, 10)