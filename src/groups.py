GROUPS = [
    {"name": "p6m", "order": 6, "mirror": True, "glide": False, "centered": False},
    {"name": "p6", "order": 6, "mirror": False, "glide": False, "centered": False},
    {"name": "p3m1", "order": 3, "mirror": True, "glide": False, "centered": False},
    {"name": "p31m", "order": 3, "mirror": True, "glide": False, "centered": False},
    {"name": "pmg", "order": 2, "mirror": True, "glide": True, "centered": False},
    {"name": "pgg", "order": 2, "mirror": False, "glide": True, "centered": False},
    {"name": "cmm", "order": 2, "mirror": True, "glide": False, "centered": True},
    {"name": "p3", "order": 3, "mirror": False, "glide": False, "centered": False},
    {"name": "p2", "order": 2, "mirror": False, "glide": False, "centered": False},
    {"name": "pm", "order": 1, "mirror": True, "glide": False, "centered": False},
    {"name": "cm", "order": 1, "mirror": True, "glide": False, "centered": True},
    {"name": "p1", "order": 1, "mirror": False, "glide": False, "centered": False},
]

GROUP_ORDER_INDEX = {g["name"]: i for i, g in enumerate(GROUPS)}
