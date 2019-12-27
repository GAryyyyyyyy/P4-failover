# -*- coding: utf-8 -*-
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
            print 'aval_id:', aval_id
            max_AIB = 0
            for j in range(0, len(matrix)): #对每个id，也是要一行一行的看，找到所有需要调整的行，然后调整他，计算一下AIB，对所有调整过的行，最大的AIB就是这个aval_id的AIB
                if matrix[j][i][0] != 0 and matrix[j][i][1] != aval_id:
                    cur_AIB = 1
                    for k in range(i+1, len(matrix[j])):
                        if matrix[j][k][1] == aval_id:
                            print j,k
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
        print 'final_id', final_id
        for j in range(0, len(matrix)): #找到了真正AIB最小的那个后，实际进行一次调整，就完成了对第i行的调整了。
            if matrix[j][i][0] != 0 and matrix[j][i][1] != final_id:
                for k in range(i+1, len(matrix[j])):
                    if matrix[j][k][1] == final_id:
                        matrix[j][i][1], matrix[j][k][1] = matrix[j][k][1], matrix[j][i][1]

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

        pre_port = temp[start_index][0]
        for m in range(start_index+1, len(temp)):
            if temp[m][0] != pre_port:
                cur_AIB += 1
                pre_port = temp[m][0]
        result.append(cur_AIB)
    print 'result:', result



if __name__ == '__main__':
    matrix = [
                [[1, 0], [1, 0], [1, 0], [2, 0], [1, 0], [2, 0]],
                [[2, 0], [1, 0], [1, 0], [2, 0], [3, 0], [4, 0]],
                [[1, 0], [2, 0], [2, 0], [2, 0], [3, 0], [2, 0]]
             ]
    per_switch_ID_assign(matrix)
    print matrix
    inconsistency_free_ID_adjust(matrix)
    print matrix
    count_AIB(matrix)