# src/visualize_heatmap.py
"""
Seaborn heatmap renderer — 2D spatial field from FreeFEM/FD CSV.

Reads the standard `time,x,y,u` CSV, interpolates each selected time snapshot
onto a regular grid (via matplotlib.tri.LinearTriInterpolator — no scipy
required), then renders each panel as a seaborn heatmap with:
  - rocket / mako / viridis colourmap (seaborn palette)
  - drawn domain boundary and, if provided, the lens/interface contour
  - physical (x, y) axes, shared colour scale across panels

This is the "seaborn heatplot" leg of the pipeline:
    Python → Docker/FreeFEM → data/solution_data.csv → Python (this module)
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import matplotlib.patheffects as pe
import seaborn as sns


def _pick_times(all_times, n):
    uniq = np.sort(np.unique(all_times))
    if n >= len(uniq):
        return uniq
    idx = np.linspace(0, len(uniq) - 1, n).round().astype(int)
    return uniq[idx]


def _interpolate_to_grid(sub, Ngx=200, Ngy=100):
    """Interpolate scattered (x,y,u) FEM data onto a regular grid."""
    g = sub.groupby(["x", "y"], as_index=False)["u"].mean()
    x, y, u = g["x"].to_numpy(), g["y"].to_numpy(), g["u"].to_numpy()
    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()

    xi = np.linspace(xmin, xmax, Ngx)
    yi = np.linspace(ymin, ymax, Ngy)
    Xi, Yi = np.meshgrid(xi, yi)

    triang = mtri.Triangulation(x, y)
    interp = mtri.LinearTriInterpolator(triang, u)
    Zi = np.asarray(interp(Xi, Yi))
    Zi = np.where(np.isfinite(Zi), Zi, 0.0)  # mask extrapolated NaN → 0
    return xi, yi, Zi


def generate_heatmap(
    csv_path=None, out_path=None, n_panels=3,
    palette="rocket",
    lens_params=None,
    title=None,
    Ngx=220, Ngy=110,
):
    """Render the scalar field as a multi-panel seaborn heatmap.

    Parameters
    ----------
    csv_path     : str   path to `time,x,y,u` CSV (default: data/solution_data.csv)
    out_path     : str   output PNG (default: data/heat_heatmap.png)
    n_panels     : int   number of time snapshots
    palette      : str   seaborn colour palette name (rocket / mako / viridis / ...)
    lens_params  : dict  optional — draw the ellipse interface on each panel.
                         Keys: x_lens, y_lens, a_lens, b_lens
    title        : str   figure suptitle
    Ngx, Ngy     : int   interpolation grid resolution
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = csv_path or os.path.join(project_root, "data", "solution_data.csv")
    out_path = out_path or os.path.join(project_root, "data", "heat_heatmap.png")

    print(f"Generating seaborn heatmap from: {csv_path}")
    df = pd.read_csv(csv_path)
    times = _pick_times(df["time"].to_numpy(), n_panels)
    n = len(times)

    # shared colour bounds
    umin = float(df["u"].min())
    umax = float(df["u"].max()) or 1.0

    cmap = sns.color_palette(palette, as_cmap=True)

    # ── figure layout ──────────────────────────────────────────────────────────
    sns.set_theme(style="white", font_scale=1.0)
    fig, axes = plt.subplots(n, 1, figsize=(10, 3.0 * n),
                             constrained_layout=True)
    if n == 1:
        axes = [axes]
    fig.patch.set_facecolor("white")

    for ax, t in zip(axes, times):
        sub = df[df["time"] == t]
        xi, yi, Zi = _interpolate_to_grid(sub, Ngx, Ngy)

        # ── seaborn heatmap (xticklabels / yticklabels from physical coords) ──
        # We subsample the axis labels so they don't overlap.
        x_ticks = np.linspace(0, Ngx - 1, 6).astype(int)
        y_ticks = np.linspace(0, Ngy - 1, 5).astype(int)
        x_labels = [f"{xi[i]:.1f}" for i in x_ticks]
        y_labels  = [f"{yi[j]:.1f}" for j in y_ticks]

        sns.heatmap(
            Zi,
            ax=ax,
            cmap=cmap,
            vmin=umin, vmax=umax,
            xticklabels=False,
            yticklabels=False,
            cbar_kws={"label": "$T$  (u.a.)", "shrink": 0.85},
        )

        # replace integer ticks with physical coordinates
        ax.set_xticks(x_ticks + 0.5)
        ax.set_xticklabels(x_labels, fontsize=8)
        ax.set_yticks(y_ticks + 0.5)
        # seaborn heatmap has y increasing downward; flip labels
        ax.set_yticklabels(y_labels[::-1], fontsize=8)

        ax.set_xlabel("$x$  (m)", fontsize=10)
        ax.set_ylabel("$y$  (m)", fontsize=10)
        ax.set_title(f"$t = {t:.2f}$ s", fontsize=12, pad=4)

        # ── optional: draw ellipse interface (lens boundary Γ_int) ───────────
        if lens_params is not None:
            xl  = lens_params["x_lens"]
            yl  = lens_params["y_lens"]
            al  = lens_params["a_lens"]
            bl  = lens_params["b_lens"]
            xmin_d, xmax_d = xi[0], xi[-1]
            ymin_d, ymax_d = yi[0], yi[-1]

            th = np.linspace(0, 2 * np.pi, 300)
            xe = xl + al * np.cos(th)
            ye = yl + bl * np.sin(th)

            # map physical coords → pixel coords
            px = (xe - xmin_d) / (xmax_d - xmin_d) * Ngx
            py = Ngy - (ye - ymin_d) / (ymax_d - ymin_d) * Ngy  # flip y
            ax.plot(px, py, color="white", lw=1.6, ls="--", alpha=0.90,
                    path_effects=[pe.withStroke(linewidth=3, foreground="black")],
                    zorder=5, label=r"$\Gamma_{\rm int}$")

        # ── domain + subdomain labels ─────────────────────────────────────────
        stroke = [pe.withStroke(linewidth=2.5, foreground="black")]
        kw = dict(fontsize=13, fontweight="bold", color="white",
                  ha="center", va="center",
                  path_effects=stroke, zorder=6, transform=ax.transData)
        if lens_params is not None:
            xl = lens_params["x_lens"]; yl = lens_params["y_lens"]
            xmin_d = xi[0]; xmax_d = xi[-1]
            ymin_d = yi[0]; ymax_d = yi[-1]
            # pixel position of lens centre
            px_c = (xl - xmin_d) / (xmax_d - xmin_d) * Ngx
            py_c = Ngy - (yl - ymin_d) / (ymax_d - ymin_d) * Ngy
            ax.text(px_c, py_c, r"$\Omega_1$", **kw)
            ax.text(Ngx * 0.12, Ngy * 0.15, r"$\Omega_2$", **kw)
        else:
            ax.text(Ngx * 0.25, Ngy * 0.5, r"$\Omega_1$", **kw)
            ax.text(Ngx * 0.75, Ngy * 0.5, r"$\Omega_2$", **kw)

    if title is None:
        title = "Champ scalaire $T(x,y,t)$ — heatmap seaborn"
    fig.suptitle(title, fontsize=13, y=1.01)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved seaborn heatmap to: {out_path}")
    return out_path
