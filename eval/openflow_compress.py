def openflow_compression(paths):
    switch_dict = {}
    count = 0
    for path in paths:
        dst = path[-1]
        for i in range(0, len(path)-1):
            cur_switch = path[i]
            next_hop = path[i+1]
            entries_list = switch_dict.get(cur_switch, [])
            if not (next_hop, dst) in entries_list:
                count = count + 1
                entries_list.append((next_hop, dst))
                switch_dict[cur_switch] = entries_list
    return count


if __name__ == '__main__':
    paths = [
        ["s1", "s2", "s3", "s4"],
        ["s2", "s3", "s4"]
    ]
    print openflow_compression(paths)