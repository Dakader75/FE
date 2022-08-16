import line_of_sight_cython

if __name__ == '__main__':
    import random, time
    grid = [False for _ in range(100)]
    num_trials = 100000 # 140 ms +/- 20 ms
    random_nums = [random.randint(0, 9) for i in range(num_trials * 4)]
    start = time.time_ns() / 1e6
    for x in range(num_trials):
        out = bool(line_of_sight_cython.get_line(
            (random_nums[x * 4], random_nums[x * 4 + 1]), 
            (random_nums[x * 4 + 2], random_nums[x * 4 + 3]),
            grid, 10))
    end = time.time_ns() / 1e6
    print(end - start)

    print(out)
