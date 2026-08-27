from .groups import GROUPS, GROUP_ORDER_INDEX

ALLOWED_GROUP_NAMES = [g["name"] for g in GROUPS]

FORCE_GROUPS_BY_SHAPE = {}
FORCE_ROTATION_ORDERS_BY_SHAPE = {}

REFERENCE_GROUPS_BY_SHAPE = {
    "hexiamond_0": ["cm"],
    "hexiamond_1": ["p2"],
    "hexiamond_2": ["cmm"],
    "hexiamond_3": ["p2", "p1"],
    "hexiamond_4": ["p2", "cm"],
    "hexiamond_5": ["p31m", "p2", "pm"],
    "hexiamond_6": ["p3", "p2"],
    "hexiamond_7": ["p2"],
    "hexiamond_8": ["p6m"],
    "hexiamond_9": ["p6", "p1"],
    "hexiamond_10": ["p2", "pm"],
    "hexiamond_11": ["p2"],
}

SCREEN_RINGS = 1
CONFIRM_RINGS = 5  
CENTER_MAX_CANDIDATES = 300
TRANSLATION_MAX_LEN = 6.0
OVERLAP_TOL = 1e-5
AREA_TOL = 1e-3
MAX_TESTS_PER_GROUP = 20000


def groups_to_search(shape_id):
    forced = FORCE_GROUPS_BY_SHAPE.get(shape_id)
    if forced:
        return [g for g in GROUPS if g["name"] in forced]
    forced_orders = FORCE_ROTATION_ORDERS_BY_SHAPE.get(shape_id)
    if forced_orders:
        return [g for g in GROUPS if g["order"] in forced_orders]
    return GROUPS