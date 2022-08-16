from math import floor
from ctypes import c_int64

# From https://github.com/lmas/opensimplex

STRETCH_CONSTANT2 = -0.211324865405187  # (1 / sqrt(2 + 1) - 1) / 2
SQUISH_CONSTANT2 = 0.366025403784439  # (sqrt(2 + 1) -1) / 2
NORM_CONSTANT2 = 47

GRADIENTS2 = [5, 2, 2, 5,
              -5, 2, -2, 5,
              5, -2, 2, -5,
              -5, -2, -2, -5]

def _overflow(x):
    return c_int64(x).value

def _init(seed):
    # Have to zero fill so we can properly loop over it later
    perm = [0] * 256
    source = list(range(256))
    # Generates a proper permutation (i.e. doesn't merely perform N
    # successive pair swaps on a base array)
    seed = _overflow(seed * 6364136223846793005 + 1442695040888963407)
    seed = _overflow(seed * 6364136223846793005 + 1442695040888963407)
    seed = _overflow(seed * 6364136223846793005 + 1442695040888963407)
    for i in range(255, -1, -1):
        seed = _overflow(seed * 6364136223846793005 + 1442695040888963407)
        r = int((seed + 31) % (i + 1))
        if r < 0:
            r += i + 1
        perm[i] = source[r]
        source[r] = source[i]
    return perm

def _extrapolate2(perm, xsb, ysb, dx, dy):
    index = perm[(perm[xsb & 0xFF] + ysb) & 0xFF] & 0x0E
    g1, g2 = GRADIENTS2[index:index + 2]
    return g1 * dx + g2 * dy

def _noise2(x, y, perm):
    # Place input coordinates onto the grid
    stretch_offset = (x + y) * STRETCH_CONSTANT2
    xs = x + stretch_offset
    ys = y + stretch_offset

    # Floor to get grid coordinates of rhombus (stretched square) super-cell origin
    xsb = floor(xs)
    ysb = floor(ys)

    # Skew out to get actual coordinates of rhombus origin.
    squish_offset = (xsb + ysb) * SQUISH_CONSTANT2
    xb = xsb + squish_offset
    yb = ysb + squish_offset

    # Compute grid coodinates relative to rhombus origin
    xins = xs - xsb
    yins = ys - ysb

    # Sum those together to get a value that determines which region we're in.
    in_sum = xins + yins

    # Positions relative to origin point
    dx0 = x - xb
    dy0 = y - yb

    value = 0

    # Contribution (1, 0)
    dx1 = dx0 - 1 - SQUISH_CONSTANT2
    dy1 = dy0 - 0 - SQUISH_CONSTANT2
    attn1 = 2 - dx1 * dx1 - dy1 * dy1
    if attn1 > 0:
        attn1 *= attn1
        value += attn1 * attn1 * _extrapolate2(perm, xsb + 1, ysb + 0, dx1, dy1)

    # Contribution (0, 1)
    dx2 = dx0 - 0 - SQUISH_CONSTANT2
    dy2 = dy0 - 1 - SQUISH_CONSTANT2
    attn2 = 2 - dx2 * dx2 - dy2 * dy2
    if attn2 > 0:
        attn2 *= attn2
        value += attn2 * attn2 * _extrapolate2(perm, xsb + 0, ysb + 1, dx2, dy2)

    if in_sum <= 1:  # we're inside the triangle (2-Simplex) at (0, 0)
        zins = 1 - in_sum
        if zins > xins or zins > yins:  # (0, 0) is one of the closest two triangular vertices
            if xins > yins:
                xsv_ext = xsb + 1
                ysv_ext = ysb - 1
                dx_ext = dx0 - 1
                dy_ext = dy0 + 1
            else:
                xsv_ext = xsb - 1
                ysv_ext = ysb + 1
                dx_ext = dx0 + 1
                dy_ext = dy0 - 1
        else:  # (1, 0) and (0, 1) are the closest two vertices
            xsv_ext = xsb + 1
            ysv_ext = ysb + 1
            dx_ext = dx0 - 1 - 2 * SQUISH_CONSTANT2
            dy_ext = dy0 - 1 - 2 * SQUISH_CONSTANT2
    else:  # We're inside the triangle (2-Simple) at (1, 1)
        zins = 2 - in_sum
        if zins < xins or zins < yins:  # (0, 0 is one of closest two triangular vertices)
            if xins > yins:
                xsv_ext = xsb + 2
                ysv_ext = ysb + 0
                dx_ext = dx0 - 2 - 2 * SQUISH_CONSTANT2
                dy_ext = dy0 + 0 - 2 * SQUISH_CONSTANT2
            else:
                xsv_ext = xsb + 0
                ysv_ext = ysb + 2
                dx_ext = dx0 + 0 - 2 * SQUISH_CONSTANT2
                dy_ext = dy0 - 2 - 2 * SQUISH_CONSTANT2
        else:  # (1, 0) and (0, 1) are the closest two vertices
            xsv_ext = xsb
            ysv_ext = ysb
            dx_ext = dx0
            dy_ext = dy0
        xsb += 1
        ysb += 1
        dx0 = dx0 - 1 - 2 * SQUISH_CONSTANT2
        dy0 = dy0 - 1 - 2 * SQUISH_CONSTANT2

    # Contribution (0, 0) or (1, 1)
    attn0 = 2 - dx0 * dx0 - dy0 * dy0
    if attn0 > 0:
        attn0 *= attn0
        value += attn0 * attn0 * _extrapolate2(perm, xsb, ysb, dx0, dy0)

    # Extra vertex
    attn_ext = 2 - dx_ext * dx_ext - dy_ext * dy_ext
    if attn_ext > 0:
        attn_ext *= attn_ext
        value += attn_ext * attn_ext * _extrapolate2(perm, xsv_ext, ysv_ext, dx_ext, dy_ext)

    return value / NORM_CONSTANT2

def get(x, y, seed):
    perm = _init(seed)
    val = _noise2(x, y, perm)
    new_val = (val - -0.865) / (.865 - -0.865)
    return new_val

if __name__ == '__main__':
    perm = _init(47)
    val = _noise2(0, 0, perm)
    print(val)

    width, height = 100, 100
    total = 0
    minimum, maximum = 0, 0
    for y in range(width):
        for x in range(height):
            val = _noise2(x, y, perm)
            if val < minimum:
                minimum = val
            if val > maximum:
                maximum = val
            total += val
            # print("%.2f " % val, end='')
        print("")
    print(total / (width * height))
    print(minimum, maximum)