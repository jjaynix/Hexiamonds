import json
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from src.shapes import HEXIAMONDS, SHAPE_IDS, SHAPE_NAMES
from src.classify import classify_shape_best

NUM_RINGS = 15


def build_tile_order(t1, t2, orbit_size, num_rings):
    entries = []
    for i in range(-num_rings, num_rings + 1):
        for j in range(-num_rings, num_rings + 1):
            shell = max(abs(i), abs(j))
            tv = i * t1 + j * t2
            dist = float(np.linalg.norm(tv))
            for k in range(orbit_size):
                entries.append({"shell": shell, "dist": dist, "imageIndex": k, "dx": float(tv[0]), "dy": float(tv[1])})
    entries.sort(key=lambda e: (e["shell"], e["dist"], e["imageIndex"]))
    return entries


def build_group_entry(result):
    center = result["center"]
    verified_images = result["distinct_images"]

    images = []
    for poly in verified_images:
        centered = poly - center
        images.append({"kind": "rot", "angle": 0.0, "polygon": centered.tolist()})

    tiles = build_tile_order(result["t1"], result["t2"], len(images), NUM_RINGS)

    return {
        "group": result["group"],
        "order": result["order"],
        "mirror": result["mirror"],
        "glide": result["glide"],
        "orbit_size": len(images),
        "upgraded_from": result.get("upgraded_from"),
        "center": center.tolist(),
        "polygon": (result["base_pts"] - center).tolist(),
        "images": images,
        "tiles": tiles,
        "t1": result["t1"].tolist(),
        "t2": result["t2"].tolist(),
    }


def build_entry(shape_id, blueprint, max_tests_per_group=None):
    t0 = time.time()
    out = classify_shape_best(shape_id, blueprint, max_tests_per_group=max_tests_per_group)
    elapsed = time.time() - t0
    if out["best_fit"] is None:
        return {"id": shape_id, "name": SHAPE_NAMES.get(shape_id, shape_id), "found": False, "search_time_seconds": elapsed}

    groups = [build_group_entry(r) for r in out["all_fits"]]

    return {
        "id": shape_id,
        "name": SHAPE_NAMES.get(shape_id, shape_id),
        "found": True,
        "group": groups[0]["group"],
        "search_time_seconds": elapsed,
        "groups": groups,
    }


def _build_entry_task(args):
    shape_id, blueprint = args
    entry = build_entry(shape_id, blueprint)
    return shape_id, entry


def export():
    tasks = list(zip(SHAPE_IDS, HEXIAMONDS))
    num_workers = min(len(tasks), os.cpu_count() or 4)
    t_total = time.time()

    entries_by_id = {}
    print(f"Running {len(tasks)} shapes across {num_workers} worker processes...")
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(_build_entry_task, task): task[0] for task in tasks}
        for future in as_completed(futures):
            shape_id, entry = future.result()
            names = [g["group"] for g in entry.get("groups", [])]
            print(f"{shape_id}: {names} ({entry.get('search_time_seconds', 0):.1f}s)")
            entries_by_id[shape_id] = entry

    entries = [entries_by_id[sid] for sid in SHAPE_IDS]

    with open("webapp/data.js", "w") as f:
        f.write("const APP_DATA = " + json.dumps({"hexiamonds": entries}, indent=2) + ";")
    print(f"wrote webapp/data.js ({time.time() - t_total:.1f}s total)")


if __name__ == "__main__":
    export()