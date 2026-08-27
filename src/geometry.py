import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from .lattice import get_triangle_vertices


def build_polygon(blueprint):
    tris = [Polygon(get_triangle_vertices(q, r, o)) for q, r, o in blueprint]
    poly = unary_union(tris)
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda p: p.area)
    return poly


def raw_triangle_edge_midpoints(blueprint):
    pts = []
    for q, r, o in blueprint:
        verts = get_triangle_vertices(q, r, o)
        for i in range(3):
            pts.append((verts[i] + verts[(i + 1) % 3]) / 2)
    uniq = []
    for p in pts:
        if not any(np.allclose(p, u, atol=1e-6) for u in uniq):
            uniq.append(np.array(p))
    return uniq


def raw_triangle_centroids(blueprint):
    pts = []
    for q, r, o in blueprint:
        verts = get_triangle_vertices(q, r, o)
        pts.append(np.mean(verts, axis=0))
    uniq = []
    for p in pts:
        if not any(np.allclose(p, u, atol=1e-6) for u in uniq):
            uniq.append(np.array(p))
    return uniq


def raw_lattice_vertices(blueprint):
    pts = []
    for q, r, o in blueprint:
        pts.extend(list(get_triangle_vertices(q, r, o)))
    uniq = []
    for p in pts:
        if not any(np.allclose(p, u, atol=1e-6) for u in uniq):
            uniq.append(np.array(p))
    return uniq


def polygon_points(blueprint):
    coords = np.array(build_polygon(blueprint).exterior.coords)
    return coords[:-1]


def rotate_points(pts, angle_deg, center):
    c = np.asarray(center)
    a = np.radians(angle_deg)
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return (pts - c) @ R.T + c


def reflect_points(pts, axis_angle_deg, point_on_axis):
    p = np.asarray(point_on_axis)
    a = np.radians(axis_angle_deg)
    d = np.array([np.cos(a), np.sin(a)])
    rel = pts - p
    proj_len = rel @ d
    proj = np.outer(proj_len, d)
    return 2 * proj - rel + p


def glide_points(pts, axis_angle_deg, point_on_axis, glide_length):
    reflected = reflect_points(pts, axis_angle_deg, point_on_axis)
    a = np.radians(axis_angle_deg)
    d = np.array([np.cos(a), np.sin(a)])
    return reflected + glide_length * d


def translate_points(pts, v):
    return pts + np.asarray(v)
