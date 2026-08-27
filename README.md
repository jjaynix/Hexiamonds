hexiamonds as prototiles of wallpaper patterns - balaoing, pineda, sarmiento

note: both run_full_study.py and export_app_data.py should take about 6 mins to run as the system searches for all wallpaper groups exhaustively (see config.py)


- `src/lattice.py` — triangular grid → Cartesian 
- `src/shapes.py` — the 12 blueprints 
- `src/geometry.py` — polygon construction + generic rotate/reflect/glide/translate on raw point arrays (not grid-restricted)
- `src/centers.py` — candidate centers, candidate lattice vectors, area-targeted lattice pairing
- `src/groups.py` — the 17 wallpaper group generator definitions.
- `src/config.py` — parameterss for running the code
- `src/classify.py` — the search engine
- `src/animate.py` — ring-by-ring reveal animation
- `parallel_runner.py` — speeds up the search process by utilizing available CPU cores
- `run_full_study.py`, `render_animation.py` — entry points