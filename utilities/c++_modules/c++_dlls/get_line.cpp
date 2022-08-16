// To compile: g++ -O2 -Wall -fPIC -shared -o libGetLine.dll get_line.cpp -lpython3.9

#define PY_SSIZE_T_CLEAN
#include <python3.9/Python.h>

#include <stdbool.h>
//#include <assert.h>

bool GetOpacity(int pos_x, int pos_y, PyObject* opacity_grid, int height) {
    // returns true when the tile is opaque
    // returns false otherwise
    unsigned int idx = pos_x * height + pos_y;
    int truthy = PyObject_IsTrue(PyList_GetItem(opacity_grid, idx));
    return (bool) truthy;
}

bool GetLine(int x1, int y1, int x2, int y2, PyObject* opacity_grid, int height)
{
    if (x1 == x2 && y1 == y2) {
        return true;
    }
    int dx = x2 - x1;
    int dy = y2 - y1;
    int x = x1, y = y1;

    int xstep = 1, ystep = 1;
    if (dy < 0) {
        ystep = -1;
        dy = -dy;
    }
    if (dx < 0) {
        xstep = -1;
        dx = -dx;
    }
    int ddy = 2 * dy, ddx = 2 * dx;

    if (ddx >= ddy) {
        int errorprev = dx, error = dx;
        for(int i = 0; i < dx; ++i) {
            x += xstep;
            error += ddy;
            // How far off the straight line to the right are you
            if (error > ddx) {
                y += ystep;
                error -= ddx;
                if (error + errorprev < ddx) {  // Bottom square
                    int pos_x = x, pos_y = y - ystep;
                    if ((pos_x != x2 && pos_y != y2) && GetOpacity(pos_x, pos_y, opacity_grid, height)) {
                        return false;
                    }
                } else if (error + errorprev > ddx) { // Left square
                    int pos_x = x - xstep, pos_y = y;
                    if ((pos_x != x2 && pos_y != y2) && GetOpacity(pos_x, pos_y, opacity_grid, height)) {
                        return false;
                    }
                } else {  // Through the middle
                    int pos1_x = x, pos1_y = y - ystep;
                    int pos2_x = x - xstep, pos2_y = y;
                    if (GetOpacity(pos1_x, pos1_y, opacity_grid, height) && GetOpacity(pos2_x, pos2_y, opacity_grid, height)) {
                        return false;
                    }
                }
            }
            if ((x != x2 && y != y2) && GetOpacity(x, y, opacity_grid, height)) {
                return false;
            }
            errorprev = error;
        }
    } else {
        int errorprev = dx, error = dy;
        for(int i = 0; i < dy; ++i) {
            y += ystep;
            error += ddx;
            if (error > ddy) {
                x += xstep;
                error -= ddy;
                if (error + errorprev < ddy) {  // Bottom square
                    int pos_x = x - xstep, pos_y = y;
                    if ((pos_x != x2 && pos_y != y2) && GetOpacity(pos_x, pos_y, opacity_grid, height)) {
                        return false;
                    }
                } else if (error + errorprev > ddy) { // Left square
                    int pos_x = x, pos_y = y - ystep;
                    if ((pos_x != x2 && pos_y != y2) && GetOpacity(pos_x, pos_y, opacity_grid, height)) {
                        return false;
                    }
                } else {  // Through the middle
                    int pos1_x = x, pos1_y = y - ystep;
                    int pos2_x = x - xstep, pos2_y = y;
                    if (GetOpacity(pos1_x, pos1_y, opacity_grid, height) && GetOpacity(pos2_x, pos2_y, opacity_grid, height)) {
                        return false;
                    }
                }
            }
            if ((x != x2 && y != y2) && GetOpacity(x, y, opacity_grid, height)) {
                return false;
            }
            errorprev = error;
        }
    }
    //assert (x == x2 && y == y2);
    return true;
}

extern "C" {
    bool get_line(int start_x, int start_y, int end_x, int end_y, PyObject *opacity_grid_list, int height)
    {
        return GetLine(start_x, start_y, end_x, end_y, opacity_grid_list, height);
    }
}
