import sys
import os
from src.shapes import HEXIAMONDS, SHAPE_IDS
from src.geometry import polygon_points
from src.classify import classify_shape
from src.animate import animate_tiling

shape_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 8
rings = int(sys.argv[2]) if len(sys.argv) > 2 else 3

shape_id = SHAPE_IDS[shape_idx]
result = classify_shape(shape_id, HEXIAMONDS[shape_idx])
if result is None:
    print(f"{shape_id}: no group found within the search budget")
    sys.exit(1)

pts = polygon_points(HEXIAMONDS[shape_idx])
os.makedirs("artifacts/animations", exist_ok=True)
out_path = f"artifacts/animations/{shape_id}_{result['group']}.gif"
animate_tiling(result, pts, rings=rings, output_path=out_path)
print(f"{shape_id}: {result['group']}, orbit size {result['orbit_size']} -> {out_path}")
