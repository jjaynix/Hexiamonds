import numpy as np
import bisect

_PAIR_CACHE = {}


def _all_pairs_sorted_by_area(vectors):
    key = id(vectors)
    cached = _PAIR_CACHE.get(key)
    if cached is not None:
        return cached
    pairs = []
    for i in range(len(vectors)):
        for j in range(len(vectors)):
            if i == j:
                continue
            t1, t2 = vectors[i], vectors[j]
            cross = abs(t1[0] * t2[1] - t1[1] * t2[0])
            if cross < 1e-9:
                continue
            pairs.append((t1, t2, cross))
    pairs.sort(key=lambda p: p[2])
    areas = [p[2] for p in pairs]
    _PAIR_CACHE[key] = (areas, pairs)
    return areas, pairs


def candidate_centers(pts, extra_pts=None):
    from .lattice import V1, V2
    verts = list(pts)
    extra = list(extra_pts) if extra_pts is not None else []
    raw = verts + extra

    extended_raw = list(raw)
    if len(pts) > 0:
        for m in range(-2, 3):
            for n in range(-2, 3):
                shift = m * V1 + n * V2
                for p in pts:
                    extended_raw.append(p + shift)

    uniq = []
    for c in extended_raw:
        if not any(np.allclose(c, u, atol=1e-6) for u in uniq):
            uniq.append(c)
    return uniq


def candidate_translations(max_index=5, min_len=0.4, max_len=9.0):
    from .lattice import V1, V2
    vecs = {}
    for m in range(-max_index, max_index + 1):
        for n in range(-max_index, max_index + 1):
            if m == 0 and n == 0:
                continue
            v = m * V1 + n * V2
            length = np.linalg.norm(v)
            if min_len < length <= max_len:
                vecs[(m, n)] = v
    return list(vecs.values())


def candidate_axis_angles(pts, center):
    return [0.0, 30.0, 60.0, 90.0, 120.0, 150.0]


def lattice_pairs(vectors, max_pairs=40):
    pairs = []
    for i in range(len(vectors)):
        for j in range(len(vectors)):
            if i == j:
                continue
            t1, t2 = vectors[i], vectors[j]
            cross = t1[0] * t2[1] - t1[1] * t2[0]
            if abs(cross) < 1e-6:
                continue
            pairs.append((t1, t2, abs(cross)))
    pairs.sort(key=lambda p: p[2])
    return pairs[:max_pairs]


def lattice_pairs_matching_area(vectors, target_area, rel_tol, max_pairs=60):
    areas, all_pairs = _all_pairs_sorted_by_area(vectors)
    delta = rel_tol * max(target_area, 1)
    lo = bisect.bisect_left(areas, target_area - delta)
    hi = bisect.bisect_right(areas, target_area + delta)
    candidates = all_pairs[lo:hi]
    candidates = sorted(candidates, key=lambda p: np.linalg.norm(p[0]) + np.linalg.norm(p[1]))
    return candidates[:max_pairs]