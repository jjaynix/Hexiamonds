import numpy as np

V1 = np.array([1.0, 0.0])
V2 = np.array([0.5, np.sqrt(3) / 2])


def grid_to_cartesian(q, r):
    return q * V1 + r * V2


def get_triangle_vertices(q, r, o):
    if o == 0:
        return np.array([grid_to_cartesian(q, r), grid_to_cartesian(q + 1, r), grid_to_cartesian(q, r + 1)])
    return np.array([grid_to_cartesian(q + 1, r), grid_to_cartesian(q + 1, r + 1), grid_to_cartesian(q, r + 1)])
