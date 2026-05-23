# src/visualize_heatmap.py
"""
Seaborn-styled 2-D heatmap renderer — physical-coordinate overlay version.

Reads the standard `time,x,y,u` CSV (from the FreeFEM or FD pipeline) and
renders N time snapshots as filled-contour panels using a seaborn colour
palette.  Domain geometry (Ω₁ elliptic lens, Ω₂ matrix) is overlaid in
physical (x, y) space so the domain decomposition is clearly visible:

  • Ω₁ (sand lens)  — blue fill (alpha=0.40) + text label
  • Ω₂ (clay matrix) — hatched overlay          + text label
  • Γ_int            — solid amber contour line  + label (first panel only)

Per-panel normalisation (each snapshot scaled to its own peak) is used by
default so that the plume shape and domain-crossing contrast are legible even
when the global peak decays by 6× across the simulation.

The seaborn colour palette is applied to the temperature field; the domain
overlay uses matplotlib in physical coordinates (no pixel mapping required).
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as mpe
import matplotlib.tri as mtri
import seaborn as sns


# ── helpers ───────────────────────────────────────────────────────────────────

def _pick_times(all_times, n):
    uniq = np.sort(np.unique(all_times))
    if n >= len(uniq):
        return uniq
    idx = np.linspace(0, len(uniq) - 1, n).round().astype(int)
    return uniq[idx]


def _frame_data(sub):
    """Deduplicate FEM nodes and return (Triangulation, u_array)."""
    g = sub.groupby(["x", "y"], as_index=False)["u"].mean()
    triang = mtri.Triangulation(g["x"].to_numpy(), g["y"].to_numpy())
    return triang, g["u"].to_numpy()


def _lens_grid(lens_params, xmin, xmax, ymin, ymax, N=400):
    """Return (xg, yg, Z) where Z = (x-xl)²/al² + (y-yl)²/bl²."""
    xg = np.linspace(xmin, xmax, N)
    yg = np.linspace(ymin, ymax, N // 2)
    Xg, Yg = np.meshgrid(xg, yg)
    xl = lens_params["x_lens"]
    yl = lens_params["y_lens"]
    al = lens_params["a_lens"]
    bl = lens_params["b_lens"]
    Z = (Xg - xl) ** 2 / al ** 2 + (Yg - yl) ** 2 / bl ** 2
    return xg, yg, Z


def _draw_domains(ax, lens_params, xmin, xmax, ymin, ymax, idx=0):
    """Overlay Ω₁ / Ω₂ / Γ_int on an axis that uses physical coordinates."""
    xl = lens_params["x_lens"]
    yl = lens_params["y_lens"]
    al = lens_params["a_lens"]
    bl = lens_params["b_lens"]

    xg, yg, Z = _lens_grid(lens_params, xmin, xmax, ymin, ymax)

    # ── Ω₁ fill (sand lens) — visible blue tint ──────────────────────────────
    ax.contourf(xg, yg, Z, levels=[0.0, 1.0],
                colors=["#60A5FA"], alpha=0.40, zorder=3)

    # ── Ω₂ hatch (clay matrix) — diagonal lines ───────────────────────────────
    Zmax = float(Z.max()) + 1.0
    cs = ax.contourf(xg, yg, Z, levels=[1.0, Zmax],
                     hatches=["///"], colors=["none"], alpha=0.0, zorder=3)
    cs.set_edgecolor("#bbbbbb")
    cs.set_linewidth(0.40)

    # ── Γ_int — solid amber line (solid > dashed for legibility) ─────────────
    ax.contour(xg, yg, Z, levels=[1.0],
               colors=["#F59E0B"], linewidths=2.2,
               linestyles="-", zorder=5)

    # ── domain labels ─────────────────────────────────────────────────────────
    stroke_blue  = [mpe.withStroke(linewidth=3, foreground="#1e3a8a")]
    stroke_black = [mpe.withStroke(linewidth=2, foreground="#000000")]

    ax.text(xl, yl, r"$\Omega_1$",
            ha="center", va="center",
            fontsize=13, fontweight="bold", color="white",
            path_effects=stroke_blue, zorder=6)

    ax.text(xmin + 0.18, ymax - 0.12, r"$\Omega_2$",
            ha="left", va="top",
            fontsize=13, fontweight="bold", color="white",
            path_effects=stroke_black, zorder=6)

    # ── Γ_int label — only on first panel ────────────────────────────────────
    if idx == 0:
        ax.text(xl - al - 0.06, yl + 0.13, r"$\Gamma_{\rm int}$",
                ha="right", va="bottom",
                fontsize=10, color="#F59E0B",
                path_effects=[mpe.withStroke(linewidth=2, foreground="#000000")],
                zorder=6)


# ── public API ────────────────────────────────────────────────────────────────

def generate_heatmap(
    csv_path=None, out_path=None, n_panels=3,
    palette="plasma",
    lens_params=None,
    per_panel_norm=True,
    title=None,
):
    """Render the scalar field as a multi-panel seaborn-styled heatmap.

    Domain geometry is drawn in physical (x, y) coordinates via contour
    overlays, so Ω₁ and Ω₂ are unambiguous regardless of temperature values.

    Parameters
    ----------
    csv_path       : str   path to `time,x,y,u` CSV
    out_path       : str   output PNG
    n_panels       : int   number of time snapshots
    palette        : str   seaborn palette (plasma / rocket / mako / viridis …)
    lens_params    : dict  {"x_lens","y_lens","a_lens","b_lens"}
    per_panel_norm : bool  if True each panel is normalised to its own peak
                           (better contrast when the plume decays over time)
    title          : str   figure suptitle
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = csv_path or os.path.join(project_root, "data", "solution_data.csv")
    out_path = out_path or os.path.join(project_root, "data", "heat_heatmap.png")

    print(f"Generating seaborn heatmap from: {csv_path}")
    df = pd.read_csv(csv_path)
    df["u"] = df["u"].clip(lower=0.0)      # drop tiny numerical negatives
    times = _pick_times(df["time"].to_numpy(), n_panels)
    n = len(times)

    cmap = sns.color_palette(palette, as_cmap=True)
    xmin, xmax = float(df["x"].min()), float(df["x"].max())
    ymin, ymax = float(df["y"].min()), float(df["y"].max())

    # global norm for shared colourbar (even with per-panel rendering)
    umax_global = float(max(df["u"].max(), 1e-9))
    global_norm = plt.Normalize(0.0, umax_global)

    # Wide domain (aquifer) → stack rows; squarish → side-by-side columns.
    domain_ar = (xmax - xmin) / max(ymax - ymin, 1e-9)
    if domain_ar >= 1.5:
        nrows, ncols = n, 1
        panel_w, panel_h = 10.0, 3.4
    else:
        nrows, ncols = 1, n
        panel_w, panel_h = 4.5, 4.0

    sns.set_theme(style="white", font_scale=1.0)
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(panel_w * ncols, panel_h * nrows),
                             constrained_layout=True)
    fig.patch.set_facecolor("white")
    axes = np.array(axes).ravel()

    for idx, (ax, t) in enumerate(zip(axes, times)):
        sub = df[df["time"] == t]
        triang, u = _frame_data(sub)

        if per_panel_norm:
            umax_loc = float(max(u.max(), 1e-9))
            norm = plt.Normalize(0.0, umax_loc)
        else:
            norm = global_norm

        # ── temperature field ─────────────────────────────────────────────────
        ax.tricontourf(triang, u, levels=60, cmap=cmap, norm=norm, zorder=1)
        # iso-contour lines help show the kink at Γ_int
        ax.tricontour(triang, u, levels=10,
                      colors="white", linewidths=0.5, alpha=0.45, zorder=2)

        # ── domain overlay ────────────────────────────────────────────────────
        if lens_params is not None:
            _draw_domains(ax, lens_params, xmin, xmax, ymin, ymax, idx=idx)

        # ── axes ──────────────────────────────────────────────────────────────
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_xlabel("$x$  (m)", fontsize=10)
        ax.set_ylabel("$y$  (m)", fontsize=10)

        if per_panel_norm:
            umax_loc = float(max(u.max(), 1e-9))
            ax.set_title(
                f"$t = {t:.2f}$ s   " + r"$(T_{\rm max}=" + f"{umax_loc:.2f})$",
                fontsize=11, pad=5,
            )
        else:
            ax.set_title(f"$t = {t:.2f}$ s", fontsize=12, pad=5)

        for sp in ax.spines.values():
            sp.set_linewidth(1.4)
            sp.set_color("#333333")

    # ── shared colorbar (global scale for reference) ──────────────────────────
    mappable = plt.cm.ScalarMappable(norm=global_norm, cmap=cmap)
    cbar = fig.colorbar(mappable, ax=list(axes),
                        shrink=0.80, aspect=30, pad=0.02)
    label = "$T$  (u.a.)" + ("  [global scale]" if per_panel_norm else "")
    cbar.set_label(label, fontsize=10)
    cbar.ax.tick_params(labelsize=9)

    if title is None:
        title = r"Champ scalaire $T(x,y,t)$ — heatmap seaborn"
    fig.suptitle(title, fontsize=12, y=1.01)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved seaborn heatmap to: {out_path}")
    return out_path
