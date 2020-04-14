import time
import cProfile

# init
PROFILE = True
DEBUG = False 
time_cost = [0] * 5

lines = open("puzzle_30x30.txt").readlines()

row_count, col_count = list(map(int, lines[0].strip().split()))
row_hints = []
col_hints = []

for line in lines[1 : 1 + row_count]:
    row_hints.append(list(map(int, line.strip().split())))

for line in lines[1 + row_count:]:
    col_hints.append(list(map(int, line.strip().split())))

grids = [[0] * col_count for i in range(row_count)]
row_locked = [False] * row_count
col_locked = [False] * col_count
row_results_all = []
col_results_all = []
row_results = [[] for i in range(row_count)]
col_results = [[] for i in range(col_count)]
last_progress_time = 0
progress = 0

# search
def print_grids():
    for row in grids:
        print("  ".join(map(str, row)))
    print("=" * 50)

def generate_line(hint, empty_count):
    results = []
    for i in range(empty_count + 1):
        prefix = [0] * i + [1 for _ in range(hint[0])]

        if len(hint) > 1:
            for rest_part in generate_line(hint[1:], empty_count - i):
                results.append(prefix + [0] + rest_part)
        else:
            results.append(prefix + [0 for _ in range(empty_count - i)])

    return results

def get_lines(line_hint, line_count):
    empty_count = line_count - (sum(line_hint) + len(line_hint) - 1);
    return generate_line(line_hint, empty_count)

def init_results_all():
    # find all possible results
    for i in range(row_count):
        row_results_all.append(get_lines(row_hints[i], col_count))

    for i in range(col_count):
        col_results_all.append(get_lines(col_hints[i], row_count))

    while True:
        # check fix grids
        is_fixed_row = [[True] * col_count for i in range(row_count)]
        is_fixed_col = [[True] * col_count for i in range(row_count)]

        for i in range(row_count):
            fix_value = row_results_all[i][0]

            for j in range(col_count):
                for result in row_results_all[i]:
                    if result[j] != fix_value[j]:
                        is_fixed_row[i][j] = False
                        break

        for i in range(col_count):
            fix_value = col_results_all[i][0]

            for j in range(row_count):
                for result in col_results_all[i]:
                    if result[j] != fix_value[j]:
                        is_fixed_col[j][i] = False
                        break

        # set fixed grids
        for i in range(row_count):
            for j in range(col_count):
                if is_fixed_row[i][j]:
                    grids[i][j] = row_results_all[i][0][j]

                if is_fixed_col[i][j]:
                    grids[i][j] = col_results_all[j][0][i]

        # filter result by fixed grids
        is_updated = False
        for i in range(row_count):
            new_results = []
            for result in row_results_all[i]:
                is_matched = True
                for j in range(col_count):
                    if is_fixed_row[i][j] or is_fixed_col[i][j]:
                        if result[j] != grids[i][j]:
                            is_matched = False
                            is_updated = True
                            break
                if is_matched:
                    new_results.append(result)

            row_results_all[i] = new_results

        for i in range(col_count):
            new_results = []
            for result in col_results_all[i]:
                is_matched = True
                for j in range(row_count):
                    if is_fixed_row[j][i] or is_fixed_col[j][i]:
                        if result[j] != grids[j][i]:
                            is_matched = False
                            is_updated = True
                            break
                if is_matched:
                    new_results.append(result)

            col_results_all[i] = new_results

        if not is_updated:
            break

def init_results():
    min_result_count = -1

    for i in range(row_count):
        row_results[i].append(row_results_all[i])

        result_count = len(row_results[i][-1])
        if min_result_count == -1 or min_result_count > result_count:
            min_result_count = result_count

    for i in range(col_count):
        col_results[i].append(col_results_all[i])

        result_count = len(col_results[i][-1])
        if min_result_count == -1 or min_result_count > result_count:
            min_result_count = result_count

    return min_result_count

def update_results(changed_pos, id, is_row = False):
    time0 = time.time()
    min_result_count = -1

    if DEBUG:
        print("changed_pos", changed_pos)

    if not is_row:
        for i in range(row_count):
            if not row_locked[i]:
                if i in changed_pos:
                    changed_pos.remove(i)
                    new_results = []
                    last_results = row_results[i][-2]

                    for result in last_results:
                        if grids[i][id] == result[id]:
                            new_results.append(result)

                    row_results[i][-1] = new_results
                    if DEBUG:
                        print("row", i, len(row_results[i]), new_results)

                result_count = len(row_results[i][-1])
                if min_result_count == -1 or min_result_count > result_count:
                    min_result_count = result_count

                    if result_count == 0:
                        return 0, changed_pos

    if is_row:
        for i in range(col_count):
            if not col_locked[i]:
                if i in changed_pos:
                    changed_pos.remove(i)
                    new_results = []
                    last_results = col_results[i][-2]

                    for result in last_results:
                        if grids[id][i] == result[id]:
                            new_results.append(result)

                    col_results[i][-1] = new_results
                    if DEBUG:
                        print("col", i, len(col_results[i]), new_results)

                result_count = len(col_results[i][-1])
                if min_result_count == -1 or min_result_count > result_count:
                    min_result_count = result_count

                    if result_count == 0:
                        return 0, changed_pos

    time_cost[0] = time_cost[0] + time.time() - time0
    time_cost[1] = time_cost[1] + 1

    return min_result_count, []

def get_next_line_id(min_result_count):
    for i in range(row_count):
        if not row_locked[i]:
            if len(row_results[i][-1]) == min_result_count:
                return i, True

    for i in range(col_count):
        if not col_locked[i]:
            if len(col_results[i][-1]) == min_result_count:
                return i, False

def find_changed_pos(line, last_line, last_changed_pos):
    result = last_changed_pos
    for i in range(len(line)):
        if line[i] != last_line[i] and not i in result:
            result.append(i)
    return result

def try_line(id, is_row, ratio):
    if DEBUG:
        print("trying %s %d" % (is_row and "row" or "col", id))

    global progress
    global last_progress_time
    if time.time() - last_progress_time > 0.2:
        last_progress_time = time.time()
        print("current progress: %.6f%%" % (progress * 100))

    line_count = is_row and col_count or row_count
    line_results = is_row and row_results[id][-1] or col_results[id][-1]
    line_record = []

    if is_row:
        row_locked[id] = True
    else:
        col_locked[id] = True

    if DEBUG:
        print("line_result", line_results)

    for i in range(line_count):
        if is_row:
            col_results[i].append([])
            line_record.append(grids[id][i])
        else:
            row_results[i].append([])
            line_record.append(grids[i][id])

    last_line = [-1] * line_count
    last_changed_pos = []

    for line in line_results:
        # check & set value
        for i in range(line_count):
            if is_row:
                grids[id][i] = line[i]
            else:
                grids[i][id] = line[i]

        # try next line
        changed_pos = find_changed_pos(line, last_line, last_changed_pos)
        last_line = line

        min_result_count, last_changed_pos = update_results(changed_pos, id, is_row)
        if DEBUG:
            print("min_result_count", min_result_count)

        if min_result_count == 0: # conflict
            progress += ratio / len(line_results)
            continue
        elif min_result_count == -1: # succeed
            print("success!")
            return True
        else:
            if DEBUG:
                print_grids()

            next_id, next_is_row = get_next_line_id(min_result_count)
            if try_line(next_id, next_is_row, ratio / len(line_results)):
                return True

    # restore value
    for i in range(line_count):
        if is_row:
            col_results[i].pop()
            grids[id][i] = line_record[i]
        else:
            row_results[i].pop()
            grids[i][id] = line_record[i]

    if is_row:
        row_locked[id] = False
    else:
        col_locked[id] = False

    if DEBUG:
        print("finish %s %d" % (is_row and "row" or "col", id))

    return False

def main():
    p = cProfile.Profile()
    if PROFILE:
        p.runcall(init_results_all)
    else:
        init_results_all()

    min_result_count = init_results()
    id, is_row = get_next_line_id(min_result_count)
 
    if PROFILE:
        p.runcall(try_line, id, is_row, 1.0)
        p.print_stats()
    else:
        try_line(id, is_row, 1.0)

    print("==result==")
    print_grids()

    print(time_cost)

if __name__ == "__main__":
    main()



