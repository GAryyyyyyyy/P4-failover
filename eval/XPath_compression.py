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
    for i in range(0, len(matrix[0])):
        aval_ids = ()
        for j in range(0, len(matrix)):
            if matrix[j][i][0] != 0:
                aval_ids.append(matrix[j][i][1])

        if len(aval_ids) == 1:
            continue

        for aval_id in aval_ids:
            for j in range(0, len(matrix)):
                if matrix[j][i][0] != 0 and matrix[j][i][1] != aval_id:
                    for k in range(1, len(matrix[j])):
                        if matrix[j][k][1] == aval_id:
                            temp = matrix[j][:]
                            temp[0][1], temp[k][1] = temp[k][1], temp[0][1]
                            temp = sorted(temp, key = lambda x: x[1])
                            




if __name__ == '__main__':
    matrix = [
                [[1, 0], [1, 0], [1, 0], [2, 0], [1, 0], [2, 0]],
                [[2, 0], [1, 0], [1, 0], [2, 0], [3, 0], [4, 0]],
                [[1, 0], [2, 0], [2, 0], [2, 0], [3, 0], [2, 0]]
             ]
    per_switch_ID_assign(matrix)
    print matrix
