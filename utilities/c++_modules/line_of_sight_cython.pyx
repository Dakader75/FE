# distutils: language=c
# cython: binding=False, boundscheck=False, wraparound=False, nonecheck=False, cdivision=True
# cython: optimize.use_switch=True

# Compile with `python line_of_sight_cython_setup.py build_ext --inplace`
# Can get cython from `pip install cython`
# Can get Windows compilation tools from Visual Studio 2019 build tools
# Follow: https://stackoverflow.com/a/50210015

cdef inline int get_pos(int x, int y, int grid_height):
    return x * grid_height + y

cdef inline bint get_line_(int x1, int y1, int x2, int y2, opacity_map, int grid_height):
    if x1 == x2 and y1 == y2:
        return True
    # SuperCover Line Algorithm http://eugen.dedu.free.fr/projects/bresenham/
    # Setup initial conditions
    cdef int i, dx, dy, x, y, xstep, ystep, ddy, ddx, errorprev, error
    dx = x2 - x1
    dy = y2 - y1
    x = x1
    y = y1

    xstep = 1
    ystep = 1
    if dy < 0:
        ystep = -1
        dy = -dy
    if dx < 0:
        xstep = -1
        dx = -dx
    ddy = 2*dy
    ddx = 2*dx

    if ddx >= ddy:
        errorprev = error = dx
        for i in range(dx):
            x += xstep
            error += ddy
            # How far off the straight line to the right are you
            if error > ddx:
                y += ystep
                error -= ddx
                if error + errorprev < ddx: # bottom square
                    if (x != x2 or y - ystep != y2) and opacity_map[get_pos(x, y - ystep, grid_height)]:
                        return False
                elif error + errorprev > ddx: # left square
                    if (x - xstep != x2 or y != y2) and opacity_map[get_pos(x - xstep, y, grid_height)]:
                        return False
                else:  # through the middle
                    if opacity_map[get_pos(x, y - ystep, grid_height)] and opacity_map[get_pos(x - xstep, y, grid_height)]:
                        return False
            if (x != x2 or y != y2) and opacity_map[get_pos(x, y, grid_height)]:
                return False
            errorprev = error
    else:
        errorprev = error = dy
        for i in range(dy):
            y += ystep
            error += ddx
            if error > ddy:
                x += xstep
                error -= ddy
                if error + errorprev < ddy: # bottom square
                    if (x - xstep != x2 or y != y2) and opacity_map[get_pos(x - xstep, y, grid_height)]:
                        return False
                elif error + errorprev > ddy: # left square
                    if (x != x2 or y - ystep != y2) and opacity_map[get_pos(x, y - ystep, grid_height)]:
                        return False
                else:  # through the middle
                    if opacity_map[get_pos(x, y - ystep, grid_height)] and opacity_map[get_pos(x - xstep, y, grid_height)]:
                        return False
            if (x != x2 or y != y2) and opacity_map[get_pos(x, y, grid_height)]:
                return False
            errorprev = error
    assert x == x2 and y == y2
    return True

cpdef get_line(tuple start, tuple end, opacity_map, int grid_height):
    return get_line_(start[0], start[1], end[0], end[1], opacity_map, grid_height)
