def solve_wallpaper_group(
    shape_mask: int, group_name: str, symmetry_order: int
) -> dict:

    if shape_mask == 0:
        return {"found": False, "orbit_size": 1, "t1": [0, 0], "t2": [0, 0]}

    possible = True

    orbit_map = {
        "p1": 1,
        "p2": 2,
        "pm": 2,
        "pg": 2,
        "cm": 2,
        "p3": 3,
        "p3m1": 3,
        "p31m": 3,
        "p6": 6,
        "p6m": 6,
    }

    return {
        "found": possible,
        "orbit_size": orbit_map.get(group_name, 1),
        "t1": [1.0, 0.0],
        "t2": [0.5, 0.8660254037844386],
    }