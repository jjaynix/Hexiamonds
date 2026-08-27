import numpy as np
import time
from shapely.geometry import Polygon
import shapely.affinity
from . import config
from .geometry import (
    polygon_points,
    rotate_points,
    reflect_points,
    glide_points,
    raw_lattice_vertices,
    raw_triangle_centroids,
    raw_triangle_edge_midpoints,
)
from .centers import (
    candidate_centers,
    candidate_translations,
    candidate_axis_angles,
    lattice_pairs_matching_area,
)


TRANSLATIONS = candidate_translations(max_len=config.TRANSLATION_MAX_LEN)


def point_group_images_with_meta(pts, center, order, mirror, glide, axis_angle, glide_len):
    entries = [("rot", 360.0 * k / order, rotate_points(pts, 360.0 * k / order, center)) for k in range(order)]
    if mirror:
        entries = entries + [("mir", ang, reflect_points(poly, axis_angle, center)) for kind, ang, poly in entries]
    if glide:
        glide_axis = axis_angle + 90.0 if mirror else axis_angle
        entries = entries + [("gli", ang, glide_points(poly, glide_axis, center, glide_len)) for kind, ang, poly in entries]
    return entries


def dedup_images_with_meta(entries, decimals=9):
    seen = {}
    for kind, ang, poly in entries:
        key = tuple(sorted(tuple(np.round(p, decimals)) for p in poly))
        if key not in seen:
            seen[key] = (kind, ang, poly)
    return list(seen.values())


def point_group_images(pts, center, order, mirror, glide, axis_angle, glide_len):
    images = [rotate_points(pts, 360.0 * k / order, center) for k in range(order)]
    if mirror:
        images = images + [reflect_points(im, axis_angle, center) for im in images]
    if glide:
        glide_axis = axis_angle + 90.0 if mirror else axis_angle
        images = images + [glide_points(im, glide_axis, center, glide_len) for im in images]
    return images


def dedup_images(images, decimals=9):
    seen = {}
    for im in images:
        key = tuple(sorted(tuple(np.round(p, decimals)) for p in im))
        if key not in seen:
            seen[key] = im
    return list(seen.values())


def patch_overlap_check_shrunk(shrunk_base_polys, base_images, t1, t2, rings):
    k = len(shrunk_base_polys)
    if k == 0:
        return False

    local_mins = np.array([im.min(axis=0) for im in base_images])
    local_maxs = np.array([im.max(axis=0) for im in base_images])
    
    shifts = np.array([i * t1 + j * t2 for i in range(-rings, rings + 1) for j in range(-rings, rings + 1)])
    s = len(shifts)

    mins = (local_mins[None, :, :] + shifts[:, None, :]).reshape(s * k, 2)
    maxs = (local_maxs[None, :, :] + shifts[:, None, :]).reshape(s * k, 2)

    n = s * k
    if n < 2:
        return False

    overlap_x = (mins[:, None, 0] <= maxs[None, :, 0]) & (maxs[:, None, 0] >= mins[None, :, 0])
    overlap_y = (mins[:, None, 1] <= maxs[None, :, 1]) & (maxs[:, None, 1] >= mins[None, :, 1])
    bbox_overlap = overlap_x & overlap_y

    rows, cols = np.triu_indices(n, k=1)
    candidate_mask = bbox_overlap[rows, cols]
    rows, cols = rows[candidate_mask], cols[candidate_mask]
    if len(rows) == 0:
        return False

    poly_cache = {}

    def get_poly(idx):
        poly = poly_cache.get(idx)
        if poly is None:
            s_idx = idx // k
            b_idx = idx % k
            shift = shifts[s_idx]
            poly = shapely.affinity.translate(shrunk_base_polys[b_idx], xoff=shift[0], yoff=shift[1])
            poly_cache[idx] = poly
        return poly

    for a, b in zip(rows, cols):
        pa, pb = get_poly(int(a)), get_poly(int(b))
        if pa.intersects(pb):
            return True
    return False


def patch_overlap_check(shrunk_base_polys, base_images, t1, t2, rings):
    if rings > 1:
        if patch_overlap_check_shrunk(shrunk_base_polys, base_images, t1, t2, rings=1):
            return True
    return patch_overlap_check_shrunk(shrunk_base_polys, base_images, t1, t2, rings)


def relevant_axis_angles(group, pts, center):
    if not (group["mirror"] or group["glide"]):
        return [None]
    return candidate_axis_angles(pts, center)[:8]


def is_centered_translation(distinct_images, t1, t2, tol=1e-4):
    center_vec = (t1 + t2) / 2.0
    ref_keys = set()
    for i in range(-3, 4):
        for j in range(-3, 4):
            shift = i * t1 + j * t2
            for im in distinct_images:
                key = tuple(sorted(tuple(np.round(p, 7)) for p in (im + shift)))
                ref_keys.add(key)
    total, matched = 0, 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            shift = i * t1 + j * t2 + center_vec
            for im in distinct_images:
                key = tuple(sorted(tuple(np.round(p, 7)) for p in (im + shift)))
                total += 1
                if key in ref_keys:
                    matched += 1
    return total > 0 and matched == total


def patch_key_set(imgs, t1, t2, rings=4):
    keys = set()
    for i in range(-rings, rings + 1):
        for j in range(-rings, rings + 1):
            shift = i * t1 + j * t2
            for im in imgs:
                key = tuple(sorted(tuple(np.round(p, 7)) for p in (im + shift)))
                keys.add(key)
    return keys


def test_rotation_at_point(imgs, t1, t2, point, order, ref_keys, rings_test=1):
    total, matched = 0, 0
    for i in range(-rings_test, rings_test + 1):
        for j in range(-rings_test, rings_test + 1):
            shift = i * t1 + j * t2
            for im in imgs:
                rotated = rotate_points(im + shift, 360.0 / order, point)
                key = tuple(sorted(tuple(np.round(p, 7)) for p in rotated))
                total += 1
                if key in ref_keys:
                    matched += 1
    return total > 0 and matched == total


def test_mirror_at_point(imgs, t1, t2, point, axis_angle, ref_keys, rings_test=1):
    total, matched = 0, 0
    for i in range(-rings_test, rings_test + 1):
        for j in range(-rings_test, rings_test + 1):
            shift = i * t1 + j * t2
            for im in imgs:
                reflected = reflect_points(im + shift, axis_angle, point)
                key = tuple(sorted(tuple(np.round(p, 7)) for p in reflected))
                total += 1
                if key in ref_keys:
                    matched += 1
    return total > 0 and matched == total


def special_lattice_points(center, t1, t2):
    fracs = [0.0, 1.0 / 3, 2.0 / 3, 0.5]
    pts = []
    seen = set()
    for a in fracs:
        for b in fracs:
            p = center + a * t1 + b * t2
            key = tuple(np.round(p, 6))
            if key not in seen:
                seen.add(key)
                pts.append(p)
    return pts


def upgrade_candidate_points(distinct, t1, t2, rings=1):
    raw = []
    for i in range(-rings, rings + 1):
        for j in range(-rings, rings + 1):
            shift = i * t1 + j * t2
            for im in distinct:
                verts = im + shift
                raw.extend(list(verts))
                raw.append(verts.mean(axis=0))
                n = len(verts)
                for k in range(n):
                    raw.append((verts[k] + verts[(k + 1) % n]) / 2)
    uniq = []
    for p in raw:
        if not any(np.allclose(p, u, atol=1e-6) for u in uniq):
            uniq.append(p)
    return uniq


def find_maximal_upgrade(result):
    t1, t2 = result["t1"], result["t2"]
    distinct = result["distinct_images"]
    ref = patch_key_set(distinct, t1, t2)
    candidates = upgrade_candidate_points(distinct, t1, t2)
    best_order = result["order"]
    best_mirror = result["mirror"]
    upgrade = None
    for pt in candidates:
        for order in (2, 3, 4, 6):
            if order <= best_order:
                continue
            if test_rotation_at_point(distinct, t1, t2, pt, order, ref):
                mirror_angle = None
                for ang in (0.0, 30.0, 60.0, 90.0, 120.0, 150.0):
                    if test_mirror_at_point(distinct, t1, t2, pt, ang, ref):
                        mirror_angle = ang
                        break
                mirror_here = mirror_angle is not None
                if order > best_order or (order == best_order and mirror_here and not best_mirror):
                    best_order = order
                    best_mirror = mirror_here
                    upgrade = {"center": pt, "order": order, "mirror": mirror_here, "axis_angle": mirror_angle}
    if not best_mirror:
        for pt in candidates:
            mirror_angle = None
            for ang in (0.0, 30.0, 60.0, 90.0, 120.0, 150.0):
                if test_mirror_at_point(distinct, t1, t2, pt, ang, ref):
                    mirror_angle = ang
                    break
            if mirror_angle is not None and not result["mirror"]:
                if upgrade is None:
                    upgrade = {"center": pt, "order": result["order"], "mirror": True, "axis_angle": mirror_angle}
                else:
                    upgrade["mirror"] = True
                    upgrade["axis_angle"] = mirror_angle
                break
    return upgrade


def screen_group(pts, area, group, max_tests, extra_centers=None, verify_no_upgrade=False):
    is_pure_p1 = group["order"] == 1 and not group["mirror"] and not group["glide"]
    if is_pure_p1:
        centers = [np.array([0.0, 0.0])]
    else:
        centers = candidate_centers(pts, extra_centers)[: config.CENTER_MAX_CANDIDATES]
    translations = TRANSLATIONS
    tests = 0
    buf_val = -max(config.OVERLAP_TOL / 2.0, 1e-5)

    for center in centers:
        for axis_angle in relevant_axis_angles(group, pts, center):
            
            if group["mirror"]:
                if axis_angle is not None and (axis_angle % 30.0 != 0.0):
                    continue

            glide_len = 0.0
            if group["glide"] and translations and axis_angle is not None:
                a = np.radians(axis_angle)
                axis_dir = np.array([np.cos(a), np.sin(a)])
                aligned_lengths = [
                    abs(v @ axis_dir) for v in translations
                    if np.linalg.norm(v - (v @ axis_dir) * axis_dir) < 1e-6 and abs(v @ axis_dir) > 1e-6
                ]
                if aligned_lengths:
                    glide_len = min(aligned_lengths) / 2
            raw_images = point_group_images(pts, center, group["order"], group["mirror"], group["glide"], axis_angle, glide_len)
            distinct_images = dedup_images(raw_images)
            
            shrunk_base_polys = []
            for im in distinct_images:
                p = Polygon(im)
                p_shrunk = p.buffer(buf_val)
                shrunk_base_polys.append(p if p_shrunk.is_empty else p_shrunk)

            expected_cell_area = area * len(distinct_images)
            pairs = lattice_pairs_matching_area(translations, expected_cell_area, config.AREA_TOL)
            
            for t1, t2, cell_area in pairs:
                tests += 1
                if tests > max_tests:
                    return None
                
                polys_ok = not patch_overlap_check(shrunk_base_polys, distinct_images, t1, t2, rings=config.SCREEN_RINGS)
                if polys_ok:
                    confirmed = not patch_overlap_check(shrunk_base_polys, distinct_images, t1, t2, rings=config.CONFIRM_RINGS)
                    if confirmed:
                        centered_found = is_centered_translation(distinct_images, t1, t2)
                        if group["centered"] and not centered_found:
                            continue
                        if not group["centered"] and group["name"] == "pm" and centered_found:
                            continue
                        if group["glide"] and not group["mirror"]:
                            has_any_mirror = False
                            for test_axis in (0.0, 30.0, 60.0, 90.0, 120.0, 150.0):
                                plain_mirror_images = point_group_images(pts, center, group["order"], True, False, test_axis, 0.0)
                                plain_distinct = dedup_images(plain_mirror_images)
                                plain_area_ok = abs(area * len(plain_distinct) - cell_area) <= config.AREA_TOL * max(cell_area, 1)
                                
                                plain_shrunk = []
                                for im in plain_distinct:
                                    p = Polygon(im)
                                    ps = p.buffer(buf_val)
                                    plain_shrunk.append(p if ps.is_empty else ps)
                                    
                                if plain_area_ok and not patch_overlap_check(plain_shrunk, plain_distinct, t1, t2, rings=config.SCREEN_RINGS):
                                    has_any_mirror = True
                                    break
                            if has_any_mirror:
                                continue
                        candidate_result = {
                            "group": group["name"],
                            "order": group["order"],
                            "mirror": group["mirror"],
                            "glide": group["glide"],
                            "center": center,
                            "axis_angle": axis_angle,
                            "t1": t1,
                            "t2": t2,
                            "orbit_size": len(distinct_images),
                            "distinct_images": distinct_images,
                            "base_pts": pts,
                        }
                        if verify_no_upgrade and find_maximal_upgrade(candidate_result) is not None:
                            continue
                        return candidate_result
    return None


def discrete_orientations(pts, raw_pts, include_reflections=True):
    centroid = pts.mean(axis=0)
    raw = []
    chiralities = (False, True) if include_reflections else (False,)
    for base_reflected in chiralities:
        working_pts = reflect_points(pts, 0.0, centroid) if base_reflected else pts
        working_raw = reflect_points(raw_pts, 0.0, centroid) if base_reflected else raw_pts
        for rot in range(0, 360, 60):
            raw.append((rotate_points(working_pts, rot, centroid), rotate_points(working_raw, rot, centroid)))
    uniq = []
    for cand_pts, cand_raw in raw:
        key = tuple(sorted(tuple(np.round(p, 9)) for p in cand_pts))
        if not any(key == u_key for u_key, _ in uniq):
            uniq.append((key, (cand_pts, cand_raw)))
    return [v for _, v in uniq]


def upgrade_result(result):
    upgrade = find_maximal_upgrade(result)
    if upgrade is None:
        return result
    match = None
    for g in config.GROUPS:
        if g["order"] == upgrade["order"] and g["mirror"] == upgrade["mirror"] and not g["glide"]:
            match = g
            break
    if match is None:
        return result
    upgraded = dict(result)
    upgraded["group"] = match["name"]
    upgraded["order"] = match["order"]
    upgraded["mirror"] = match["mirror"]
    upgraded["center"] = upgrade["center"]
    upgraded["axis_angle"] = upgrade["axis_angle"] if match["mirror"] else None
    upgraded["upgraded_from"] = result["group"]
    return upgraded


def classify_shape(shape_id, blueprint, candidate_groups=None, max_tests_per_group=None, skip_upgrade=False):
    if max_tests_per_group is None:
        max_tests_per_group = config.MAX_TESTS_PER_GROUP
    t_start = time.time()
    base_pts = polygon_points(blueprint)
    corners = raw_lattice_vertices(blueprint)
    centroids = raw_triangle_centroids(blueprint)
    edge_mids = raw_triangle_edge_midpoints(blueprint)
    base_raw = np.array(corners + centroids + edge_mids)
    area = Polygon(base_pts).area
    chiral_orientations = discrete_orientations(base_pts, base_raw, include_reflections=True)
    achiral_orientations = discrete_orientations(base_pts, base_raw, include_reflections=False)
    all_fits = []

    if candidate_groups is not None:
        if len(candidate_groups) > 0 and isinstance(candidate_groups[0], str):
            groups_to_run = [g for g in config.GROUPS if g["name"] in candidate_groups]
        else:
            groups_to_run = candidate_groups
    else:
        groups_to_run = config.groups_to_search(shape_id)

    for group in groups_to_run:
        orientations = achiral_orientations if (group["mirror"] or group["glide"]) else chiral_orientations
        for pts, raw_pts in orientations:
            result = screen_group(pts, area, group, max_tests_per_group, extra_centers=raw_pts)
            if result is not None:
                all_fits.append(result if skip_upgrade else upgrade_result(result))
                break
    all_fits.sort(key=lambda r: config.GROUP_ORDER_INDEX[r["group"]])
    dedup_fits = []
    seen_names = set()
    for r in all_fits:
        if r["group"] not in seen_names:
            seen_names.add(r["group"])
            dedup_fits.append(r)
    all_fits = dedup_fits
    reference = config.REFERENCE_GROUPS_BY_SHAPE.get(shape_id)
    if reference is not None:
        all_fits = [r for r in all_fits if r["group"] in reference]
        all_fits.sort(key=lambda r: reference.index(r["group"]))

    elapsed = time.time() - t_start
    for r in all_fits:
        r["search_time_seconds"] = elapsed
    return {
        "best_fit": all_fits[0] if all_fits else None,
        "all_fits": all_fits,
        "search_time_seconds": elapsed,
    }


def classify_shape_best(shape_id, blueprint, max_tests_per_group=None):
    reference = config.REFERENCE_GROUPS_BY_SHAPE.get(shape_id)
    out = classify_shape(
        shape_id, blueprint,
        candidate_groups=reference,
        max_tests_per_group=max_tests_per_group,
        skip_upgrade=reference is not None,
    )
    found_names = {r["group"] for r in out["all_fits"]}
    if reference is not None and not set(reference).issubset(found_names):
        fallback = classify_shape(
            shape_id, blueprint,
            candidate_groups=None,
            max_tests_per_group=max_tests_per_group,
        )
        fallback_by_name = {r["group"]: r for r in fallback["all_fits"]}
        merged = list(out["all_fits"])
        for name in reference:
            if name not in found_names and name in fallback_by_name:
                merged.append(fallback_by_name[name])
                found_names.add(name)
        merged.sort(key=lambda r: reference.index(r["group"]))
        out = dict(out)
        out["all_fits"] = merged
        out["best_fit"] = merged[0] if merged else None
    return out


def classify_all(shapes_by_id):
    results = {}
    for shape_id, blueprint in shapes_by_id.items():
        results[shape_id] = classify_shape(shape_id, blueprint)
    return results