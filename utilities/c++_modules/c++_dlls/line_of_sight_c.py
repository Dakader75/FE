import ctypes
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
fn = dir_path + "/libGetLine.dll"
handle = ctypes.pydll.LoadLibrary(fn)

handle.get_line.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.py_object, ctypes.c_int]

def get_line(start: tuple, end: tuple, opacity_grid: list, height: int) -> bool:
    return handle.get_line(start[0], start[1], end[0], end[1], opacity_grid, height)

if __name__ == '__main__':
    import random, time
    grid = [False for _ in range(100)]
    num_trials = 100000  # 280 +/- 30 ms
    random_nums = [random.randint(0, 9) for i in range(num_trials * 4)]
    start = time.time_ns() / 1e6
    for x in range(num_trials):
        out = bool(get_line(
            (random_nums[x * 4], random_nums[x * 4 + 1]), 
            (random_nums[x * 4 + 2], random_nums[x * 4 + 3]),
            grid, 10))
    end = time.time_ns() / 1e6
    print(end - start)

    print(out)
