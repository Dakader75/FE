# distutils: language=c
# cython: binding=False, boundscheck=False, wraparound=False, nonecheck=False, cdivision=True
# cython: optimize.use_switch=True
# encoding: utf-8

cimport cython
from cython.parallel cimport prange

import pygame
from pygame.surfarray import pixels3d

cdef int THREADS = 4

# Colorkey definition
cdef unsigned char COLORKEY_R = 128
cdef unsigned char COLORKEY_G = 160
cdef unsigned char COLORKEY_B = 128

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cdef inline void invert_surface(unsigned char[:, :, :] rgb_array):
    """
    Takes a surface (rgb_array) and inverts the color of the pixels
    Expects r, g, b array to be size w x h x 3
    """

    cdef Py_ssize_t w, h
    w, h = rgb_array.shape[:2]

    cdef:
        int i=0, j=0
        unsigned char *r
        unsigned char *g
        unsigned char *b

    with nogil:
        for j in prange(h, schedule="static", num_threads=THREADS):
            for i in range(w):
                r = &rgb_array[i, j, 0]
                g = &rgb_array[i, j, 1]
                b = &rgb_array[i, j, 2]
                if r[0] != COLORKEY_R and g[0] != COLORKEY_G and b[0] != COLORKEY_B:
                    r[0] = 255 - r[0]
                    g[0] = 255 - g[0]
                    b[0] = 255 - b[0]

cpdef inline void invert(object surface_):
    invert_surface(pixels3d(surface_))
