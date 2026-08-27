import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from src.classify import classify_shape_best
from src.shapes import HEXIAMONDS, SHAPE_IDS, SHAPE_NAMES
from src import config


def process_single_shape(task_args):
    shape_id, blueprint = task_args
    t0 = time.time()

    out = classify_shape_best(shape_id, blueprint)

    elapsed = time.time() - t0
    return shape_id, out, elapsed


def generate_report():
    os.makedirs("artifacts", exist_ok=True)
    start_total = time.time()

    tasks = list(zip(SHAPE_IDS, HEXIAMONDS))
    num_workers = os.cpu_count() or 4

    print(f"running across {num_workers} CPU workers...\n")

    results_dict = {}

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_shape = {
            executor.submit(process_single_shape, task): task[0]
            for task in tasks
        }

        for future in as_completed(future_to_shape):
            shape_id = future_to_shape[future]
            try:
                s_id, out, elapsed = future.result()
                results_dict[s_id] = out

                fits = out.get("all_fits", [])
                verified_groups = ", ".join(f["group"] for f in fits) if fits else "None"

                print(
                    f"   / {s_id:<12} | "
                    f"verified ({len(fits)}): {verified_groups:<12} | time: {elapsed:.2f}s"
                )
            except Exception as e:
                print(f"error processing {shape_id}: {e}")

    rows = [
        "| Shape | Group | Rotation Order | Mirror | Glide | Orbit Size |",
        "|---|---|---|---|---|---|",
    ]

    for shape_id in SHAPE_IDS:
        name = SHAPE_NAMES.get(shape_id, shape_id)
        out = results_dict.get(shape_id)
        fits = out.get("all_fits") if out else None
        if not fits:
            rows.append(f"| {name} | none found | - | - | - | - |")
            continue

        for result in fits:
            rows.append(
                f"| {name} | {result['group']} | {result['order']} | "
                f"{'yes' if result['mirror'] else 'no'} | {'yes' if result['glide'] else 'no'} | "
                f"{result['orbit_size']} |"
            )

    with open("artifacts/wallpaper_group_report.md", "w") as f:
        f.write("# results\n\n")
        f.write("\n".join(rows) + "\n")

    print(
        f"\n complete execution time: {time.time() - start_total:.2f}s"
    )


if __name__ == "__main__":
    generate_report()