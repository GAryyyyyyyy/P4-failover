import random
import time

import eval_topo
import dijkstra_base

def _edge_fail(topo, edge):
    dst_node = random.choice(list(topo.nodes))
    dijkstra_base.shortest_path_with_failure(topo, None, edge[1], dst_node)
    dijkstra_base.shortest_path_with_failure(topo, edge, edge[1], edge[0])
    dijkstra_base.shortest_path_with_failure(topo, edge, edge[1], dst_node)


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
        len_failed = dijkstra_base.shortest_path_with_failure(topo, edge, edge[0], edge[1])
        total_len += (len_failed - len_normal)
        len_failed = dijkstra_base.shortest_path_with_failure(topo, edge, edge[1], edge[0])
        total_len += (len_failed - len_normal)

    avg_len = total_len / len(topo.edges)
    print avg_len
    # failed_edges = []
    # # print topo.edges
    # while True:
    #     for edge in topo.edges:
    #         if random.random() <= 0.05:
    #             print edge
    #             failed_edges.append(edge)
    #             _edge_fail(topo, edge)
    #     topo.remove_edges_from(failed_edges)
    #     print len(topo.edges)
    #     time.sleep(20)


if __name__ == '__main__':
    topo = eval_topo.vl2_topo(16)
    eval_avg_recovery_len(topo)