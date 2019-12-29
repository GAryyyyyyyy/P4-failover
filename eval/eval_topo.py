# -*- coding: utf-8 -*-

import networkx as nx

def fat_tree_topo(n=4):
    """Standard fat tree topology
    n: number of pods
    total n^3/4 servers
    total 5*n^2/4 switches
    total 3*n^3/4 links
    """
    topo = nx.Graph()
    num_of_edge_switches = n // 2
    num_of_aggregation_switches = num_of_edge_switches
    num_of_core_switches = int((n / 2) * (n / 2))

    # generate topo pod by pod
    for i in range(n):
        for j in range(num_of_edge_switches):
            topo.add_node("Pod {} edge switch {}".format(i, j))
            topo.add_node("Pod {} aggregation switch {}".format(i, j))

    # add edge among edge and aggregation switch within pod
    for i in range(n):
        for j in range(num_of_aggregation_switches):
            for k in range(num_of_edge_switches):
                topo.add_edge("Pod {} aggregation switch {}".format(i, j),
                              "Pod {} edge switch {}".format(i, k))
                # print topo.nodes["Pod {} aggregation switch {}".format(i, j)]
                topo.nodes["Pod {} aggregation switch {}".format(i, j)]["Pod {} edge switch {}".format(i, k)] = len(topo.nodes["Pod {} aggregation switch {}".format(i, j)]) + 1
                topo.nodes["Pod {} edge switch {}".format(i, k)]["Pod {} aggregation switch {}".format(i, j)] = len(topo.nodes["Pod {} edge switch {}".format(i, k)]) + 1
                # print topo.nodes["Pod {} aggregation switch {}".format(i, j)]

    # add edge among core and aggregation switch
    num_of_core_switches_connected_to_same_aggregation_switch = num_of_core_switches // num_of_aggregation_switches
    for i in range(num_of_core_switches):
        topo.add_node("Core switch {}".format(i))
        aggregation_switch_index_in_pod = i // num_of_core_switches_connected_to_same_aggregation_switch
        for j in range(n):
            topo.add_edge(
                "Core switch {}".format(i),
                "Pod {} aggregation switch {}".format(
                    j, aggregation_switch_index_in_pod))
            topo.nodes["Core switch {}".format(i)]["Pod {} aggregation switch {}".format(j, aggregation_switch_index_in_pod)] = len(topo.nodes["Core switch {}".format(i)]) + 1
            topo.nodes["Pod {} aggregation switch {}".format(j, aggregation_switch_index_in_pod)]["Core switch {}".format(i)] = len(topo.nodes["Pod {} aggregation switch {}".format(j, aggregation_switch_index_in_pod)]) + 1

    topo.name = "fat-tree({})".format(n)

    return topo

def vl2_topo(port_num_of_aggregation_switch=4):
    """Standard vl2 topology
    """
    topo = nx.Graph()
    num_of_aggregation_switches = port_num_of_aggregation_switch
    num_of_intermediate_switches = num_of_aggregation_switches // 2
    num_of_tor_switches = (port_num_of_aggregation_switch //
                           2) * (port_num_of_aggregation_switch // 2)

    # create intermediate switch
    for i in range(num_of_intermediate_switches):
        topo.add_node("Intermediate switch {}".format(i))

    # create aggregation switch
    for i in range(num_of_aggregation_switches):
        topo.add_node("Aggregation switch {}".format(i))
        for j in range(num_of_intermediate_switches):
            topo.add_edge("Aggregation switch {}".format(i),
                          "Intermediate switch {}".format(j))
            topo.nodes["Aggregation switch {}".format(i)]["Intermediate switch {}".format(j)] = len(topo.nodes["Aggregation switch {}".format(i)]) + 1
            topo.nodes["Intermediate switch {}".format(j)]["Aggregation switch {}".format(i)] = len(topo.nodes["Intermediate switch {}".format(j)]) + 1


    # create ToR switch
    num_of_tor_switches_per_aggregation_switch_can_connect = num_of_aggregation_switches // 2
    for i in range(num_of_tor_switches):
        topo.add_node("ToR switch {}".format(i))
        # every ToR only need to connect 2 aggregation switch
        aggregation_index = (
            i // num_of_tor_switches_per_aggregation_switch_can_connect) * 2
        topo.add_edge("ToR switch {}".format(i),
                      "Aggregation switch {}".format(aggregation_index))
        topo.nodes["ToR switch {}".format(i)]["Aggregation switch {}".format(aggregation_index)] = len(topo.nodes["ToR switch {}".format(i)]) + 1
        topo.nodes["Aggregation switch {}".format(aggregation_index)]["ToR switch {}".format(i)] = len(topo.nodes["Aggregation switch {}".format(aggregation_index)]) + 1

        aggregation_index += 1  # The second aggregation switch
        topo.add_edge("ToR switch {}".format(i),
                      "Aggregation switch {}".format(aggregation_index))
        topo.nodes["ToR switch {}".format(i)]["Aggregation switch {}".format(aggregation_index)] = len(topo.nodes["ToR switch {}".format(i)]) + 1
        topo.nodes["Aggregation switch {}".format(aggregation_index)]["ToR switch {}".format(i)] = len(topo.nodes["Aggregation switch {}".format(aggregation_index)]) + 1

    topo.name = 'VL2'

    return topo



def AB_fat_tree_topo(n=4):
    """Standard fat tree topology
    n: number of pods
    total n^3/4 servers
    """
    topo = nx.Graph()
    num_of_edge_switches = n // 2
    num_of_aggregation_switches = num_of_edge_switches
    num_of_core_switches = int((n / 2) * (n / 2))

    # generate topo pod by pod
    for i in range(n):
        for j in range(num_of_edge_switches):
            topo.add_node("Pod {} edge switch {}".format(i, j))
            topo.add_node("Pod {} aggregation switch {}".format(i, j))

    # add edge among edge and aggregation switch within pod
    for i in range(n):
        for j in range(num_of_aggregation_switches):
            for k in range(num_of_edge_switches):
                topo.add_edge("Pod {} aggregation switch {}".format(i, j),
                              "Pod {} edge switch {}".format(i, k))
                # print topo.nodes["Pod {} aggregation switch {}".format(i, j)]
                topo.nodes["Pod {} aggregation switch {}".format(i, j)]["Pod {} edge switch {}".format(i, k)] = len(topo.nodes["Pod {} aggregation switch {}".format(i, j)]) + 1
                topo.nodes["Pod {} edge switch {}".format(i, k)]["Pod {} aggregation switch {}".format(i, j)] = len(topo.nodes["Pod {} edge switch {}".format(i, k)]) + 1
                # print topo.nodes["Pod {} aggregation switch {}".format(i, j)]

    # add edge among core and aggregation switch
    # AB胖树和传统胖树不一样的地方就在aggregation和core的连接方式上
    # 我们要把pod按照A，B，A，B分，然后B改用新的连接方式j, j+p^i j+2p^i...
    p = n // 2 # 构造AB胖树需要的参数
    num_of_core_switches_connected_to_same_aggregation_switch = num_of_core_switches // num_of_aggregation_switches
    for i in range(num_of_core_switches):
        topo.add_node("Core switch {}".format(i))

    for i in range(n):
        if i % 2 == 0: # type A
            for j in range(num_of_edge_switches):
                for k in range(j*p, (j+1)*p):
                    topo.add_edge("Pod {} aggregation switch {}".format(i, j), "Core switch {}".format(k))
                    topo.nodes["Pod {} aggregation switch {}".format(i, j)]["Core switch {}".format(k)] = len(topo.nodes["Pod {} aggregation switch {}".format(i, j)]) + 1
                    topo.nodes["Core switch {}".format(k)]["Pod {} aggregation switch {}".format(i, j)] = len(topo.nodes["Core switch {}".format(k)]) + 1
        else: # type B 
            for j in range(num_of_edge_switches):
                index = 0
                k = j + index * p # 这里 i 为 1，所以p^1 = p
                while k < num_of_core_switches:
                    topo.add_edge("Pod {} aggregation switch {}".format(i, j), "Core switch {}".format(k))
                    topo.nodes["Pod {} aggregation switch {}".format(i, j)]["Core switch {}".format(k)] = len(topo.nodes["Pod {} aggregation switch {}".format(i, j)]) + 1
                    topo.nodes["Core switch {}".format(k)]["Pod {} aggregation switch {}".format(i, j)] = len(topo.nodes["Core switch {}".format(k)]) + 1
                    index += 1
                    k = j + index * p

    topo.name = "AB-fat-tree({})".format(n)

    return topo

def topology_zoo_topo(gml_file):
    topo = nx.readwrite.read_gml(gml_file)
    for edge in topo.edges:
        node0 = edge[0]
        node1 = edge[1]
        topo.nodes[node0][node1] = len(topo.nodes[node0]) + 1
        topo.nodes[node1][node0] = len(topo.nodes[node1]) + 1

    return topo

if __name__ == '__main__':
    topo = fat_tree_topo()