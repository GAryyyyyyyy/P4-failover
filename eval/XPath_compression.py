# -*- coding: utf-8 -*-

# Step 1 code
def path_analysis(path, path_set):
    disjoint = True
    path_sw = path[0]
    path_port = path[1]
    converge_p = None
    for p in path_set:
        p_sw = p[0]
        p_port = p[1]
        for i in range(0, len(path_sw)):
            if path_sw[i] in p_sw:
                disjoint = False
                if i == len(path_port):
                    break # 如果path中的最后一个元素出现在p中，就没啥好判断的了，去看其他的p就行了
                j = p_sw.index(path_sw[i])
                if j != len(p_port) and path_port[i] != p_port[j]:
                    return 0 # 端口不一样，不行！ 
                # i j 是第一个相同元素出现的地方，从i+1 j+1 开始往后比较看看什么情况
                i += 1
                j += 1
                while i<len(path_sw):
                    if j<len(p_sw):
                        if path_sw[i] == p_sw[j]:
                            if i == len(path_port) or j == len(p_port) or path_port[i] == p_port[j]: # 如果已经到了最后一个交换机了，端口是不需要判断的！
                                i += 1
                                j += 1
                                continue
                            else:
                                return 0 # 交换机一样但出口不一样，不行！
                        else:
                            return 0 # 交换机不一样，不行！
                    else:
                        if path_sw[i] in p_sw:
                            return 0 # p已经走到底了，path唯一的可能就是往后面接上，但如果path后面的交换机在p中曾经出现过，那就是不合法的！这样就绕回去了。
                        i += 1


    if disjoint:
        return 2
    return 1
    
def path_aggragation(paths):
    path_sets = []
    for path in paths:
        is_path_aggregated = False
        for existing_path_set in path_sets:
            result = path_analysis(path, existing_path_set)
            if result > 0: # convergent or disjoint
                is_path_aggregated = True
                existing_path_set.append(path)
                break
        if not is_path_aggregated:
            path_sets.append([path]) # 如果path不是上面的两种情况，那他就成为了一个新的path set

    # print 'path sets', path_sets
    return path_sets


#将第一步的结果转换为第二步的输入
def dict2list(matrix):
    l = []
    for value in matrix.itervalues():
        l.append(value)
    return l

def path_sets2matrix(path_sets):
    matrix = {}
    for index in range(len(path_sets)):
        for path in path_sets[index]:
            path_sw = path[0]
            path_port = path[1]
            for i in range(0,len(path_port)):
                if matrix.get(path_sw[i]) == None:
                    matrix[path_sw[i]] = [[0,0] for m in range(len(path_sets))]
                matrix.get(path_sw[i])[index][0] = path_port[i]
            if matrix.get(path_sw[-1]) == None:
                matrix[path_sw[-1]] = [[0,0] for n in range(len(path_sets))]
    matrix = dict2list(matrix)
    # print matrix
    return matrix



# Step 2 code
def per_switch_ID_assign(matrix):
    for row in matrix:
        index = 1
        assigned_sum = 0
        cur_port = 1
        for out_port, path_id in row:
            if out_port == 0:
                assigned_sum += 1

        while assigned_sum < len(row):
            for cell in row:
                if cell[0] == cur_port:
                    cell[1] = index
                    index += 1
                    assigned_sum += 1
            cur_port += 1

def inconsistency_free_ID_adjust(matrix):
    #首先，一列一列的调整，也就是一条边一条边的看
    for i in range(0, len(matrix[0])):
        aval_ids = set() #计算所有的可能
        for j in range(0, len(matrix)):
            if matrix[j][i][0] != 0:
                aval_ids.add(matrix[j][i][1])

        if len(aval_ids) == 1: #如果只有一种可能，那就是没冲突，不用调整，跳过
            continue

        final_id = 0
        min_AIB = 999999999
        for aval_id in aval_ids: #尝试每一种可能的方式，要找到AIB最小的那种
            # print 'aval_id:', aval_id
            max_AIB = 0
            for j in range(0, len(matrix)): #对每个id，也是要一行一行的看，找到所有需要调整的行，然后调整他，计算一下AIB，对所有调整过的行，最大的AIB就是这个aval_id的AIB
                if matrix[j][i][0] != 0 and matrix[j][i][1] != aval_id:
                    cur_AIB = 1
                    for k in range(i+1, len(matrix[j])):
                        if matrix[j][k][1] == aval_id:
                            # print j,k
                            matrix[j][i][1], matrix[j][k][1] = matrix[j][k][1], matrix[j][i][1] #进行更换
                            temp = sorted(matrix[j], key = lambda x: x[1]) #这里进行排序是为了让id连续，从而可以根据端口的变化来判定AIB是否增加，id连续了，只要端口变化，AIB就要++
                            start_index = 0
                            while start_index < len(temp):
                                if(temp[start_index][1]!=0):
                                    break
                                start_index += 1

                            pre_port = temp[start_index][0]
                            for m in range(start_index+1, len(temp)):
                                if temp[m][0] != pre_port:
                                    cur_AIB += 1
                                    pre_port = temp[m][0]
                            if cur_AIB > max_AIB:
                                max_AIB = cur_AIB
                            matrix[j][k][1], matrix[j][i][1] = matrix[j][i][1], matrix[j][k][1] #模拟完此次结果需要换回去

            if max_AIB <= min_AIB:
                min_AIB = max_AIB
                final_id = aval_id
        # print 'final_id', final_id
        for j in range(0, len(matrix)): #找到了真正AIB最小的那个后，实际进行一次调整，就完成了对第i行的调整了。
            if matrix[j][i][0] != 0 and matrix[j][i][1] != final_id:
                for k in range(i+1, len(matrix[j])):
                    if matrix[j][k][1] == final_id:
                        matrix[j][i][1], matrix[j][k][1] = matrix[j][k][1], matrix[j][i][1]

# result calculate code
def count_AIB(matrix):
    result = []
    for row in matrix:
        cur_AIB =1
        temp = sorted(row, key = lambda x: x[1])
        start_index = 0
        while start_index < len(temp):
            if(temp[start_index][1]!=0):
                break
            start_index += 1
        if start_index >= len(temp): # 这一行全是0的话就不用考虑了，直接跳过。
            result.append(0)
            continue
        pre_port = temp[start_index][0]
        for m in range(start_index+1, len(temp)):
            if temp[m][0] != pre_port:
                cur_AIB += 1
                pre_port = temp[m][0]
        result.append(cur_AIB)
    print 'XPath compression result:', result
    return result


def XPath_compression(paths):
    path_sets = path_aggragation(paths)
    matrix = path_sets2matrix(path_sets)
    per_switch_ID_assign(matrix)
    inconsistency_free_ID_adjust(matrix)
    result = count_AIB(matrix)
    sum_AIB = 0
    for i in result:
        sum_AIB += i
    return float(sum_AIB) / len(result)


if __name__ == '__main__':
    paths = [
        [ [1, 2, 3, 4], [1, 1, 1] ],
        [ [4, 3, 2, 1], [1, 1, 1] ],
        [ [6, 4, 5], [1, 1] ]
    ]
    path_sets = path_aggragation(paths)
    matrix = path_sets2matrix(path_sets)
    print 'step 2 input matrix', matrix
    # matrix = [
    #             [[1, 0], [1, 0], [1, 0], [2, 0], [1, 0], [2, 0]],
    #             [[2, 0], [1, 0], [1, 0], [2, 0], [3, 0], [4, 0]],
    #             [[1, 0], [2, 0], [2, 0], [2, 0], [3, 0], [2, 0]],
    #             [[1, 0], [2, 0], [2, 0], [2, 0], [3, 0], [2, 0]],
    #             [[1, 0], [2, 0], [2, 0], [2, 0], [3, 0], [2, 0]],
    #             [[1, 0], [2, 0], [2, 0], [2, 0], [3, 0], [2, 0]],
    #             [[1, 0], [2, 0], [2, 0], [2, 0], [3, 0], [2, 0]]
    #          ]
    per_switch_ID_assign(matrix)
    print 'step 2.1 output', matrix
    inconsistency_free_ID_adjust(matrix)
    print 'step 2.2 output', matrix
    count_AIB(matrix)