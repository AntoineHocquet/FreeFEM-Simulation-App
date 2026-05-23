# src/visualize_surface.py
"""
3D "nappe de valeurs" (height-field surface) renderer.

Reads the standard `time,x,y,u` CSV produced by the Dockerized-FreeFEM step
and draws the scalar field u as a 3D triangular surface (u plotted as height
z), using matplotlib's mplot3d `plot_trisurf`. By default it lays out three
time snapshots side-by-side so the temporal evolution is visible.

This is the third leg of the pipeline:
    Python -> Docker/FreeFEM -> data/solution_data.csv -> Python (this module)
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri


def _pick_times(all_times, n):
    """Pick n times spread evenly across the available range (incl. ends)."""
    uniq = np.sort(np.unique(all_times))
    if n >= len(uniq):
        return uniq
    idx = np.linspace(0, len(uniq) - 1, n).round().astype(int)
    return uniq[idx]


def _frame_mesh(sub):
    """Return (triangulation, z) for one time slice, deduplicating vertices.

    The FreeFEM CSV emits 3 vertices per triangle, so physical nodes repeat
    across rows; we average u over identical (x, y) and triangulate the unique
    node set with Delaunay.
    """
    g = sub.groupby(["x", "y"], as_index=False)["u"].mean()
    triang = mtri.Triangulation(g["x"].to_numpy(), g["y"].to_numpy())
    return triang, g["u"].to_numpy()


def generate_surface(csv_path=None, out_path=None, n_panels=3,
                     cmap="viridis", elev=30, azim=-72,
                     title=None, zlabel="u"):
    """Render the solution as a 3D surface ("nappe de valeurs").

    Parameters
    ----------
    csv_path : str   path to a `time,x,y,u` CSV (default: data/solution_data.csv)
    out_path : str   output PNG (default: data/heat_surface.png)
    n_panels : int   number of time snapshots to draw side-by-side
    cmap     : str   matplotlib colormap
    elev,azim: float 3D view angles
    title    : str   figure suptitle (default derived from file)
    zlabel   : str   label of the vertical axis
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = csv_path or os.path.join(project_root, "data", "solution_data.csv")
    out_path = out_path or os.path.join(project_root, "data", "heat_surface.png")

    print(f"Generating 3D surface from: {csv_path}")
    df = pd.read_csv(csv_path)
    times = _pick_times(df["time"].to_numpy(), n_panels)
    n = len(times)

    umin = float(df["u"].min())
    umax = float(df["u"].max())
    span = (umax - umin) or 1.0
    norm = plt.Normalize(umin, umax + 0.05 * span)

    fig = plt.figure(figsize=(5.0 * n, 4.6))
    fig.patch.set_facecolor("white")

    for i, t in enumerate(times):
        triang, z = _frame_mesh(df[df["time"] == t])
        ax = fig.add_subplot(1, n, i + 1, projection="3d")

        ax.plot_trisurf(
            triang, z,
            cmap=cmap, norm=norm,
            linewidth=0.10, edgecolor="0.3",
            antialiased=True, shade=True,
        )

        ax.set_zlim(umin, umax + 0.05 * span)
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(f"$t = {t:.2f}$", fontsize=12, pad=2)
        ax.set_xlabel("$x$", fontsize=9, labelpad=2)
        ax.set_ylabel("$y$", fontsize=9, labelpad=2)
        ax.set_zlabel(f"${zlabel}$", fontsize=9, labelpad=2)
        ax.tick_params(labelsize=7)
        # lighten the 3D panes for a cleaner "nappe" look
        for pane in (ax.xaxis, ax.yaxis, ax.zaxis):
            pane.pane.set_facecolor((1, 1, 1, 0))
            pane.pane.set_edgecolor((0.8, 0.8, 0.8, 1))

    # shared colorbar
    mappable = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(mappable, ax=fig.axes, shrink=0.6, aspect=24, pad=0.02)
    cbar.set_label(f"${zlabel}$", fontsize=10)
    cbar.ax.tick_params(labelsize=8)

    if title is None:
        title = "Champ de solution — nappe de valeurs 3D"
    fig.suptitle(title, fontsize=13, y=0.98)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved 3D surface to: {out_path}")
    return out_path
