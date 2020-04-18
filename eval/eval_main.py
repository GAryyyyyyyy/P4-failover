# -*- coding: utf-8 -*-

import random
import time
import datetime
import eval_topo
import dijkstra_base
import XPath_compression
import eval_backup_config_calculate
import eval_fail_recovery

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
    start_time = time.time()
    for path in paths_normal:
        s = path[0]
        next_hop = path[1]
        d = path[-1]
        path_failover = dijkstra_base.shortest_path_with_first_hop_failure(topo, s, d, next_hop)
        if len(path_failover) > 0:
            paths_failover.append(path_failover)
    end_time = time.time()
    print end_time - start_time
    # print len(paths_failover)

    entry_sum = 0
    paths_XPath = []
    for path in paths_failover:
        entry_sum += len(path) - 1
        paths_XPath.append(_path2XPath_path(topo, path))

    print 'Naive 1:1 avg memory overhead:', float(entry_sum) / len(topo.nodes)
    # for h in paths_XPath:
    #     print h
    start_time = time.time()
    compression_result = XPath_compression.XPath_compression(paths_XPath)
    end_time = time.time()
    print end_time - start_time
    print 'XPath compression memory overhead:', compression_result

    port_sum = 0
    for node in topo.nodes:
        port_sum += len(topo.nodes[node])
    
    print 'Our solution memory overhead:', float(port_sum) / len(topo.nodes)


def eval_recovery_path_length_overhead(topo, sample_sum = 100):
    path_overhead_sum_optimal = 0
    path_overhead_sum_our_solution = 0
    sample_count = 0
    while sample_count < sample_sum:
        node_pair = random.sample(list(topo.nodes), 2) # 随机选取 源节点 和 目的节点
        selected_path = dijkstra_base.shortest_path_with_dst_dijkstra(topo, node_pair[0], node_pair[1])
        # 利用dijkstra算出第一跳故障后的最优（最短）恢复路径
        path_length_origin = len(selected_path)
        path_length_failover = len(dijkstra_base.shortest_path_with_first_hop_failure(topo, selected_path[0], selected_path[-1], selected_path[1]))
        if path_length_failover == 0: #说明这个点无法进行故障恢复，直接跳过了
            continue
        path_overhead_sum_optimal += ( path_length_failover - path_length_origin )
    
        # 使用我们的port-based恢复方法，计算路径开销
        path_overhead_our_solution = len(dijkstra_base.port_based_recovery_path_dijkstra(topo, selected_path[0], selected_path[1])) -1 - 1
        path_overhead_sum_our_solution += path_overhead_our_solution
        sample_count += 1

    # print 'Optimal avg path length overhead: {} hops/fail'.format( float(path_overhead_sum_optimal) / sample_sum )
    # print 'Our solution avg path length overhead: {} hops/fail'.format( float(path_overhead_sum_our_solution) / sample_sum )
    return float(path_overhead_sum_optimal) / sample_sum, float(path_overhead_sum_our_solution) / sample_sum 

def _topo_wrapper(topo):
    # 由于备份路径的计算需要每条边有个name属性，所以在这里加上了
    for edge in topo.edges:
        topo[edge[0]][edge[1]]['name'] = 'HAHA'

def eval_backup_config_calculation_overhead(topo):
    _topo_wrapper(topo)
    calculation_overhead_sum = 0
    for i in range(10):
        start_time = time.time()
        eval_backup_config_calculate.calculate_backup_configs(topo)
        end_time = time.time()
        calculation_overhead_sum += (end_time - start_time)
    print 'Back up configuration calculation time:', calculation_overhead_sum / 10


def eval_fail_recovery_rate(topo):
    naive_recoveryed_rate_sum = 0
    port_based_recoveryed_rate_sum = 0
    iteration_time = 0
    while iteration_time < 10:
        flows = eval_fail_recovery.random_flows(topo, 100)
        failed_edges = eval_fail_recovery.fail_model(topo, 0.028)
        naive_recoveryed_rate = eval_fail_recovery.naive_fail_recovery(topo, flows, failed_edges)
        port_based_recoveryed_rate = eval_fail_recovery.port_based_fail_recovery(topo, flows, failed_edges)
        if naive_recoveryed_rate == -1:
            continue # 说明这次没有流受到故障的影响
        iteration_time += 1
        naive_recoveryed_rate_sum += naive_recoveryed_rate
        port_based_recoveryed_rate_sum += port_based_recoveryed_rate
    
    print 'Recovery Rate Result:'
    print 'Naive recovery rate: {:.2f} %'.format(naive_recoveryed_rate_sum / 10 * 100)
    print 'Port based recovery rate: {:.2f} %'.format(port_based_recoveryed_rate_sum / 10 * 100)

if __name__ == '__main__':
    # topo = eval_topo.topology_zoo_topo('./topology_zoo_topo/Xspedius.gml')
    topo = eval_topo.vl2_topo(64)
    print 'Topo:', topo.name
    print '# of switches:', len(topo.nodes)
    print '# of links:', len(topo.edges)
    eval_memory_overhead(topo)

    # optimal_sum = 0
    # our_solution_sum = 0
    # for i in range(10):
    #     optimal, our_solution = eval_recovery_path_length_overhead(topo, 100)
    #     optimal_sum += optimal
    #     our_solution_sum += our_solution

    # print 'Optimal avg path length overhead: {} hops/fail'.format( optimal_sum / 10 )
    # print 'Our solution avg path length overhead: {} hops/fail'.format( our_solution_sum / 10 )

    # eval_backup_config_calculation_overhead(topo)

    # eval_fail_recovery_rate(topo)
    
