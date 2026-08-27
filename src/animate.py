import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Polygon as MplPolygon

BG_COLOR = "#0f172a"
COLORS = ["#38bdf8", "#a78bfa", "#f472b6", "#fbbf24", "#34d399", "#fb7185"]
EDGE_COLOR = "#ffffff"


def build_reveal_order(distinct_images, t1, t2, rings):
    entries = []
    for i in range(-rings, rings + 1):
        for j in range(-rings, rings + 1):
            shift = i * t1 + j * t2
            shell = max(abs(i), abs(j))
            for k, im in enumerate(distinct_images):
                entries.append((shell, np.linalg.norm(shift), k, im + shift))
    entries.sort(key=lambda e: (e[0], e[1], e[2]))
    return entries


def animate_tiling(result, base_pts, rings=4, output_path="tiling.gif", fps=20, frames_per_tile=1):
    distinct_images = result["distinct_images"]
    t1, t2 = result["t1"], result["t2"]
    entries = build_reveal_order(distinct_images, t1, t2, rings)

    all_pts = np.vstack([e[3] for e in entries])
    margin = 1.0
    xmin, ymin = all_pts.min(axis=0) - margin
    xmax, ymax = all_pts.max(axis=0) + margin

    fig, ax = plt.subplots(figsize=(9, 9), facecolor=BG_COLOR)
    ax.set_aspect("equal")
    ax.set_facecolor(BG_COLOR)
    ax.axis("off")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    patches = []
    for shell, dist, k, pts in entries:
        color = COLORS[k % len(COLORS)]
        patch = MplPolygon(pts, closed=True, facecolor=color, edgecolor=EDGE_COLOR, linewidth=0.8, alpha=0.0, zorder=2)
        ax.add_patch(patch)
        patches.append(patch)

    total_frames = len(patches) * frames_per_tile

    def init():
        return patches

    def update(frame):
        idx = frame // frames_per_tile
        local_t = (frame % frames_per_tile) / frames_per_tile
        for i in range(min(idx + 1, len(patches))):
            target_alpha = 0.85
            if i == idx:
                patches[i].set_alpha(target_alpha * local_t)
            else:
                patches[i].set_alpha(target_alpha)
        return patches

    ani = animation.FuncAnimation(fig, update, frames=total_frames, init_func=init, blit=True, interval=1000 / fps)
    output_path = output_path.replace(".mp4", ".gif")
    ani.save(output_path, writer="pillow", fps=fps, dpi=110)
    plt.close(fig)
    return output_path
