# -*- coding: utf-8 -*-

import random
import dijkstra_base


def fail_type_analysis(flows, edges):
    d = {}
    for flow in flows:
        count = 0
        for i in range(0, len(flow)-1):
            if (flow[i], flow[i+1]) in edges or (flow[i+1], flow[i]) in edges:
                count += 1
        d[count] = d.get(count, 0) + 1
    print d


def random_flows(topo, num_of_flows = 50):
    flows = []
    for i in range(num_of_flows):
        node_pair = random.sample(list(topo.nodes), 2) # 随机选取 源节点 和 目的节点
        flows.append(dijkstra_base.shortest_path_with_dst_dijkstra(topo, node_pair[0], node_pair[1]))
    return flows

def normal_flows(topo, failed_edges, num_of_flows = 50, len_lower_bound = 1):
    flows = random_flows(topo, 10 * num_of_flows)
    result = []
    for flow in flows:
        edges = set()
        for i in range(0,len(flow) - 1):
            edges.add((flow[i],flow[i+1]))
            edges.add((flow[i+1],flow[i]))
        if len(edges & failed_edges) == 0 and len(flow) > len_lower_bound:
            result.append(flow)
            if len(result) == num_of_flows:
                return result
    return result


def fail_model(topo, fail_rate = 0.054):
    failed_edges = set()
    for edge in topo.edges:
        if random.random() <= fail_rate:
            failed_edges.add(edge)

    # print len(failed_edges)
    # print len(topo.edges)
    return failed_edges


def _port_based_fail_recovery(topo, flow, failed_edges, failover_from):
    for i in range(0, len(flow) - 1):
        if (flow[i], flow[i+1]) in failed_edges or (flow[i+1], flow[i]) in failed_edges:
            #说明下一跳出故障了,使用基于端口的恢复方式
            failover_from.add((flow[i], flow[i+1 ]))
            failover_from.add((flow[i+1], flow[i]))
            recovery_path = dijkstra_base.port_based_recovery_path_dijkstra(topo, flow[i], flow[i+1])
            if i+2 < len(flow):
                new_flow_path = recovery_path + flow[i+2:]
            else:
                new_flow_path = recovery_path

            edges = set()
            for j in range(0,len(new_flow_path) - 1):
                edges.add((new_flow_path[j],new_flow_path[j+1]))
                edges.add((new_flow_path[j+1],new_flow_path[j]))

            if len(edges & failover_from) != 0:
                return -1

            if len(edges & failed_edges) == 0:
                return 1
            else:
                return _port_based_fail_recovery(topo, new_flow_path, failed_edges, failover_from)
    return 1 # 成功恢复

def port_based_fail_recovery(topo, flows, failed_edges):
    affected_flows = []
    for flow in flows:
        edges = set()
        for i in range(0,len(flow) - 1):
            edges.add((flow[i],flow[i+1]))
            edges.add((flow[i+1],flow[i]))
        if len(edges & failed_edges) != 0:
            affected_flows.append(flow)
    
    if len(affected_flows) == 0:
        return -1

    recoveryed_flows = []
    for flow in affected_flows:
        if _port_based_fail_recovery(topo, flow, failed_edges, set()) == 1:
            recoveryed_flows.append(flow)

    print 'Port-based recovered flows:'
    fail_type_analysis(recoveryed_flows, failed_edges)
    
    # print 'Port based recovery result:'
    # print len(affected_flows)
    # print len(recoveryed_flows)
    return float(len(recoveryed_flows)) / len(affected_flows)

def port_based_n_link_fail(topo, flows, failed_edges, n):
    count = 0
    for flow in flows:
        edges = set()
        for i in range(0,len(flow) - 1):
            edges.add((flow[i],flow[i+1]))
        selected_edges = random.sample(edges, n)
        for edge in selected_edges:
            failed_edges.add(edge)
        if _port_based_fail_recovery(topo, flow, failed_edges, set()) == 1:
            count += 1
        for edge in selected_edges:
            failed_edges.remove(edge)
    return count
        

def _naive_fail_recovery(topo, flow, failed_edges):
    for i in range(0, len(flow) - 1):
        if (flow[i], flow[i+1]) in failed_edges or (flow[i+1], flow[i]) in failed_edges:
            #说明下一跳出故障了
            recovery_path = dijkstra_base.shortest_path_with_first_hop_failure(topo, flow[i], flow[-1], flow[i+1])
            edges = set()
            for j in range(0,len(recovery_path) - 1):
                edges.add((recovery_path[j],recovery_path[j+1]))
                edges.add((recovery_path[j+1],recovery_path[j]))
            if len(edges & failed_edges) == 0:
                return 1
            break
    return -1

def naive_fail_recovery(topo, flows, failed_edges):
    affected_flows = []
    for flow in flows:
        edges = set()
        for i in range(0,len(flow) - 1):
            edges.add((flow[i],flow[i+1]))
            edges.add((flow[i+1],flow[i]))
        if len(edges & failed_edges) != 0:
            affected_flows.append(flow)

    if len(affected_flows) == 0:
        return -1

    print 'Failed flows:'
    fail_type_analysis(affected_flows, failed_edges)

    recoveryed_flows = []
    for flow in affected_flows:
        if _naive_fail_recovery(topo, flow, failed_edges) == 1:
            recoveryed_flows.append(flow)
        # for i in range(0, len(flow) - 1):
        #     if (flow[i], flow[i+1]) in failed_edges or (flow[i+1], flow[i]) in failed_edges:
        #         #说明下一跳出故障了
        #         recovery_path = dijkstra_base.shortest_path_with_first_hop_failure(topo, flow[i], flow[-1], flow[i+1])
        #         edges = set()
        #         for j in range(0,len(recovery_path) - 1):
        #             edges.add((recovery_path[j],recovery_path[j+1]))
        #             edges.add((recovery_path[j+1],recovery_path[j]))
        #         if len(edges & failed_edges) == 0:
        #             recoveryed_flows.append(flow)
        #         break

    
    print 'Naive recovered flows:'
    fail_type_analysis(recoveryed_flows, failed_edges)
    # print len(flows)
    # print 'Naive recovery result:'
    # print len(affected_flows)
    # print len(recoveryed_flows)
    return float(len(recoveryed_flows)) / len(affected_flows)

def naive_n_link_fail(topo, flows, failed_edges, n):
    count = 0
    for flow in flows:
        edges = set()
        for i in range(0,len(flow) - 1):
            edges.add((flow[i],flow[i+1]))
        selected_edges = random.sample(edges, n)
        for edge in selected_edges:
            failed_edges.add(edge)
        if _naive_fail_recovery(topo, flow, failed_edges) == 1:
            count += 1
        for edge in selected_edges:
            failed_edges.remove(edge)
    return count