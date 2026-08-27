import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Tuple

import python_bitboard_engine as fast_wallpaper_engine


def worker_task(task_args: Tuple[int, str, Dict]) -> Dict:
    """executing the compiled search kernel."""
    shape_id, group_name, shape_data = task_args

    result = fast_wallpaper_engine.solve_wallpaper_group(
        shape_data["bitmask"], group_name, shape_data["symmetry_order"]
    )

    return {
        "shape_id": shape_id,
        "group": group_name,
        "found": result["found"],
        "orbit_size": result["orbit_size"],
        "t1": result["t1"],
        "t2": result["t2"],
    }


def run_parallel_screening(shapes: List[Dict], groups: List[str]) -> List[Dict]:
    """distributing shape x group evaluation across all CPU cores."""
    tasks = []
    for shape in shapes:
        for group in groups:
            tasks.append((shape["id"], group, shape))

    num_workers = os.cpu_count() or 4
    results = []

    print(
        f"launching {len(tasks)} tasks across {num_workers} parallel CPU processes..."
    )

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_task, task) for task in tasks]

        for future in as_completed(futures):
            try:
                res = future.result()
                results.append(res)
            except Exception as e:
                print(f"error processing task: {e}")

    return results