from heapq import heappop, heappush

def shortest_path_dijkstra(topo, s):
    paths = []
    q = [(0, s, [])]
    visited = []
    while len(visited) < len(topo.nodes):
        cost, node, path = heappop(q)
        if node not in visited:
            visited.append(node)
            path = path[:]
            path.append(node)
            if len(path) > 1:
                paths.append(path)
            # print cost, path
            for new_node in topo.adj[node]:
                if new_node not in visited:
                    heappush(q, (cost + 1, new_node, path))
    return paths


def shortest_path_with_dst_dijkstra(topo, s, d):
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
    return path

def port_based_recovery_path_dijkstra(topo, s, d):
    topo.remove_edge(s, d)

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
    
    topo.add_edge(s, d)

    if node == d:
        return path
    else:
        return [] 


def shortest_path_with_first_hop_failure(topo, s, d, next_hop):
    topo.remove_edge(s, next_hop)

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

    topo.add_edge(s, next_hop)
    
    if node == d:
        return path
    else:
        return [] 
