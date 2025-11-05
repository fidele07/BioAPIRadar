import numpy as np
from scipy.spatial import cKDTree

def get_line_equation(x, y, x0, y0, x1, y1, segment=False):
    if x1 - x0 == 0:
        x_l = np.repeat(x0, len(y))
        if y0 < y1:
            y_l = y
        else:
            y_l = y[::-1]
    else:
        m = (y1 - y0) / (x1 - x0)
        b = y0 - m * x0
        if x0 < x1:
            x_l = x
        else:
            x_l = x[::-1]
        y_l = m * x_l + b

    if segment:
        if x0 < x1:
            ix = np.logical_and(x_l >= x0, x_l <= x1)
        else:
            ix = np.logical_and(x_l >= x1, x_l <= x0)

        if y0 < y1:
            iy = np.logical_and(y_l >= y0, y_l <= y1)
        else:
            iy = np.logical_and(y_l >= y1, y_l <= y0)

        ij = np.logical_and(ix, iy)
        x_l = x_l[ij]
        y_l = y_l[ij]

    return x_l, y_l

def nearest_neighbor_max_radius(points, values, new_points, max_radius):
    tree = cKDTree(points)
    dst, ix = tree.query(
            new_points, distance_upper_bound=max_radius
        )
    val = np.full(new_points.shape[0], np.nan)
    mask = np.isfinite(dst)
    val[mask] = values[ix[mask]]

    return val

