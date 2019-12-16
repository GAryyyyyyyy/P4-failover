from heapq import heappop, heappush

def shortest_path_with_failure(topo, failed_edge, s, d):
    if failed_edge != None:
        topo.remove_edge(failed_edge[0], failed_edge[1])

    q = [(0, s, [])]
    visited = []
    while q:
        cost, node, path = heappop(q)
        if node not in visited:
            visited.append(node)
            path = path[:]
            path.append(node)
            if node == d:
                break
            for new_node in topo.adj[node]:
                if new_node not in visited:
                    heappush(q, (cost + 1, new_node, path))

    # if node == d:
        # print path
    # else:
    #     print 0 

    if failed_edge != None:
        topo.add_edge(failed_edge[0], failed_edge[1])
    
    return len(path) - 1

def avg_path_length_dijkstra(topo, s):
    total_length = 0
    q = [(0, s, [])]
    visited = []
    while len(visited) < len(topo.nodes):
        cost, node, path = heappop(q)
        if node not in visited:
            visited.append(node)
            total_length += cost
            path = path[:]
            path.append(node)
            # print cost, path
            for new_node in topo.adj[node]:
                if new_node not in visited:
                    heappush(q, (cost + 1, new_node, path))
    avg_length = float(total_length) / (len(topo.nodes) - 1)
    # print avg_length
    return avg_length