import matplotlib.pyplot as plt
import networkx as nx

def fat_tree_topo(n=4):
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

    topo.name = 'fat-tree'

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

    # create ToR switch
    num_of_tor_switches_per_aggregation_switch_can_connect = num_of_aggregation_switches // 2
    for i in range(num_of_tor_switches):
        topo.add_node("ToR switch {}".format(i))
        # every ToR only need to connect 2 aggregation switch
        aggregation_index = (
            i // num_of_tor_switches_per_aggregation_switch_can_connect) * 2
        topo.add_edge("ToR switch {}".format(i),
                      "Aggregation switch {}".format(aggregation_index))
        aggregation_index += 1  # The second aggregation switch
        topo.add_edge("ToR switch {}".format(i),
                      "Aggregation switch {}".format(aggregation_index))
        
    topo.name = 'VL2'

    return topo


