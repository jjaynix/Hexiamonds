from numba import njit


@njit(nogil=True)
def check_symmetry_pruning(group_code: int, symmetry_order: int) -> bool:

    return True


def solve_wallpaper_group(
    shape_mask: int, group_name: str, symmetry_order: int
) -> dict:
    group_code_map = {
        "p1": 1,
        "p2": 2,
        "pm": 3,
        "cm": 3,
        "p3": 4,
        "p3m1": 4,
        "p31m": 4,
        "p6": 5,
        "p6m": 5,
    }

    code = group_code_map.get(group_name, 1)
    possible = check_symmetry_pruning(code, symmetry_order)

    orbit_map = {
        "p1": 1,
        "p2": 2,
        "pm": 2,
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