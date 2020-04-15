import time
import cProfile

# init
PROFILE = True
DEBUG = True

lines = open("puzzle_50x50.txt").readlines()

row_count, col_count = list(map(int, lines[0].strip().split()))
row_hints = []
col_hints = []

for line in lines[1 : 1 + row_count]:
    row_hints.append(list(map(int, line.strip().split())))

for line in lines[1 + row_count:]:
    col_hints.append(list(map(int, line.strip().split())))

grids = [[9] * col_count for i in range(row_count)]
row_locked = [False] * row_count
col_locked = [False] * col_count
row_results_all = [[] for i in range(row_count)]
col_results_all = [[] for i in range(col_count)]
row_results = [[] for i in range(row_count)]
col_results = [[] for i in range(col_count)]
last_progress_time = 0
progress = 0

# search
def print_grids():
    for row in grids:
        print("  ".join(map(str, row)))
    print("=" * 50)

def generate_line(hint, line_limit, empty_count):
    results = []
    for i in range(empty_count + 1):
        prefix = [0] * i + [1 for _ in range(hint[0])]

        limit_ok = True
        for j in range(len(prefix)):
            if line_limit[j] != 9 and line_limit[j] != prefix[j]:
                limit_ok = False
                break

        extra_check_count = (len(hint) > 1) and 1 or empty_count - i
        extra_check_count = min(extra_check_count, len(line_limit) - len(prefix))
        for j in range(extra_check_count):
            limit = line_limit[len(prefix) + j]
            if limit != 9 and limit != 0:
                limit_ok = False
                break

        if not limit_ok:
            continue

        if len(hint) > 1:
            for rest_part in generate_line(hint[1:], line_limit[len(prefix) + 1:], empty_count - i):
                results.append(prefix + [0] + rest_part)
        else:
            results.append(prefix + [0 for _ in range(empty_count - i)])

    return results

def get_lines(line_hint, line_limit, line_count):
    empty_count = line_count - (sum(line_hint) + len(line_hint) - 1)
    results = generate_line(line_hint, line_limit, empty_count)
    # if DEBUG:
    #     print(line_hint, line_limit, results)

    return results

def get_col(id):
    result = []
    for i in range(row_count):
        result.append(grids[i][id])
    return result

def init_fixed_grids():
    for i in range(row_count):
        empty_count = col_count - (sum(row_hints[i]) + len(row_hints[i]) - 1)

        col_id = -1
        for hint in row_hints[i]:
            col_id = col_id + hint
            if hint > empty_count:
                for j in range(hint - empty_count):
                    grids[i][col_id - j] = 1
            col_id = col_id + 1

    for i in range(col_count):
        empty_count = row_count - (sum(col_hints[i]) + len(col_hints[i]) - 1)

        row_id = -1
        for hint in col_hints[i]:
            row_id = row_id + hint
            if hint > empty_count:
                for j in range(hint - empty_count):
                    grids[row_id - j][i] = 1
            row_id = row_id + 1

    if DEBUG:
        print_grids()

def check_fix_grids(fix_value, line):
    for i in range(len(line)):
        if fix_value[i] == -1:
            fix_value[i] = line[i]
            continue

        if fix_value[i] != 9 and fix_value[i] != line[i]:
            fix_value[i] = 9

    return fix_value

def generate_fixed_grids(hint, line_limit, empty_count):
    fix_value = [-1] * len(line_limit)

    is_valid = False
    for i in range(empty_count + 1):
        prefix = [0] * i + [1 for _ in range(hint[0])]

        limit_ok = True
        for j in range(len(prefix)):
            if line_limit[j] != 9 and line_limit[j] != prefix[j]:
                limit_ok = False
                break

        extra_check_count = (len(hint) > 1) and 1 or empty_count - i
        extra_check_count = min(extra_check_count, len(line_limit) - len(prefix))
        for j in range(extra_check_count):
            limit = line_limit[len(prefix) + j]
            if limit != 9 and limit != 0:
                limit_ok = False
                break

        if not limit_ok:
            continue

        if len(hint) > 1:
            is_valid2, fix_value2 = generate_fixed_grids(hint[1:], line_limit[len(prefix) + 1:], empty_count - i)
            if is_valid2:
                is_valid = True
                fix_value = check_fix_grids(fix_value, prefix + [0] + fix_value2)
        else:
            is_valid = True
            fix_value = check_fix_grids(fix_value, prefix + [0 for _ in range(empty_count - i)])

    return is_valid, fix_value

def get_fixed_grids(line_hint, line_limit, line_count):
    empty_count = line_count - (sum(line_hint) + len(line_hint) - 1)
    is_valid, fix_value = generate_fixed_grids(line_hint, line_limit, empty_count)
    # if DEBUG:
    #     if line_limit != fix_value:
    #         print(line_hint, is_valid)
    #         print(line_limit)
    #         print(fix_value)

    if not is_valid:
        fix_value = [9] * line_count

    return fix_value

def init_results_all():
    init_fixed_grids()

    while True:
        is_updated = False
        for i in range(row_count):
            fix_value = get_fixed_grids(row_hints[i], grids[i], col_count)
            for j in range(col_count):
                if fix_value[j] != 9 and grids[i][j] != fix_value[j]: # do not overwrite value set by col
                    grids[i][j] = fix_value[j]
                    is_updated = True

        for i in range(col_count):
            fix_value = get_fixed_grids(col_hints[i], get_col(i), row_count)
            for j in range(row_count):
                if fix_value[j] != 9 and grids[j][i] != fix_value[j]: # do not overwrite value set by row
                    grids[j][i] = fix_value[j]
                    is_updated = True

        if DEBUG:
            print_grids()

        if not is_updated:
            break

    for i in range(row_count):
        row_results_all[i] = get_lines(row_hints[i], grids[i], col_count)
        if DEBUG:
            print("line count for row %d: %d" % (i, len(row_results_all[i])))

    for i in range(col_count):
        col_results_all[i] = get_lines(col_hints[i], get_col(i), row_count)
        if DEBUG:
            print("line count for col %d: %d" % (i, len(col_results_all[i])))

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

    #return
    min_result_count = init_results()
    id, is_row = get_next_line_id(min_result_count)
 
    if PROFILE:
        p.runcall(try_line, id, is_row, 1.0)
        p.print_stats()
    else:
        try_line(id, is_row, 1.0)

    print("==result==")
    print_grids()

if __name__ == "__main__":
    main()



