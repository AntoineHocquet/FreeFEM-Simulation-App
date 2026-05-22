"""SPRIND figure pack driver.

`simulate --figures sprind` runs the seven simulations that are anchored to
specific figures of Hecht et al., *FreeFEM++ documentation* (v3.20) and emits
publication-quality PNGs into ``data/sprind_figures/`` plus optional animated
GIFs into ``data/sprind_figures/animations/``.

Each recipe shells out to `run_simulation(pde, domain)` (defined in
``simulate.py``), reads the resulting CSV from ``data/``, and renders the
figure with matplotlib using a consistent style:

    * single-column LaTeX size  (4.5 x 3.5 inches per panel)
    * 300 dpi
    * tight bbox, transparent background
    * ``viridis`` for non-negative scalar fields, ``coolwarm`` for signed
      fields, monochrome for mesh-only plots.

If a FreeFEM simulation fails (e.g. Docker not available or an .edp error),
the corresponding figure is skipped with a warning and the rest continues.
This keeps the driver useful for iterative development.
"""

from __future__ import annotations

import os
import shutil
import sys
import traceback
from contextlib import contextmanager
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
import pandas as pd

# We import from the same package so the relative paths work in both the
# installed entry point ("simulate") and direct script invocation.
from simulate import (
    CATALOGUE,
    DATA_DIR,
    PROJECT_ROOT,
    run_simulation,
)
from visualize_eigenmodes import render_eigenmode_grid


# ---------------------------------------------------------------------------
#  Output layout & styling
# ---------------------------------------------------------------------------
SPRIND_DIR = os.path.join(DATA_DIR, "sprind_figures")
ANIM_DIR = os.path.join(SPRIND_DIR, "animations")
FIGURES_DIR_PUBLIC = os.path.join(PROJECT_ROOT, "figures")

FIG_INCHES_SINGLE = (4.5, 3.5)
FIG_INCHES_TWOPANEL = (9.0, 3.5)
DPI = 300


def _ensure_dirs():
    os.makedirs(SPRIND_DIR, exist_ok=True)
    os.makedirs(ANIM_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR_PUBLIC, exist_ok=True)


def _savefig(fig, name: str):
    """Save ``fig`` as both PNG and PDF inside ``data/sprind_figures/``."""
    base = os.path.join(SPRIND_DIR, name)
    fig.savefig(base + ".png", dpi=DPI, bbox_inches="tight", transparent=True)
    fig.savefig(base + ".pdf", bbox_inches="tight", transparent=True)
    # Mirror PNGs into figures/ at the repo root so external repos can grab
    # them by direct path.
    shutil.copyfile(base + ".png", os.path.join(FIGURES_DIR_PUBLIC, name + ".png"))
    plt.close(fig)
    print(f"  -> {base}.png  (+ .pdf, mirrored to figures/)")


@contextmanager
def _step(label: str):
    print(f"\n[sprind] {label}")
    try:
        yield
    except Exception as exc:  # noqa: BLE001
        print(f"  !! skipped: {exc}")
        traceback.print_exc(limit=2)


def _load_csv(name: str) -> Optional[pd.DataFrame]:
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    return pd.read_csv(path)


def _stash_csv(src_name: str, dest_name: str) -> None:
    """Copy ``data/<src_name>`` to ``data/sprind_figures/_csv/<dest_name>``.

    Keeps the per-figure CSVs around even when the driver runs later
    simulations that would overwrite ``solution_data.csv``.
    """
    src = os.path.join(DATA_DIR, src_name)
    if not os.path.exists(src):
        return
    csv_cache = os.path.join(SPRIND_DIR, "_csv")
    os.makedirs(csv_cache, exist_ok=True)
    shutil.copyfile(src, os.path.join(csv_cache, dest_name))


def _final_frame(df: pd.DataFrame) -> pd.DataFrame:
    last_t = df["time"].max()
    return df[df["time"] == last_t]


def _triplot(ax, x, y, u, cmap="viridis", levels=20, signed=False):
    triang = mtri.Triangulation(x, y)
    if signed:
        amax = max(abs(np.nanmin(u)), abs(np.nanmax(u))) or 1.0
        return ax.tricontourf(triang, u, levels=levels, cmap=cmap,
                              vmin=-amax, vmax=amax)
    return ax.tricontourf(triang, u, levels=levels, cmap=cmap)


# ---------------------------------------------------------------------------
#  Figure 1 — heat-exchanger solution
#    SPRIND ref: Appendix C.1.3 iii (multi-material steady heat)
#    FreeFEM doc: Fig. 3.2, p. 25
# ---------------------------------------------------------------------------
def fig_heat_exchanger() -> None:
    run_simulation(pde="heat_multimaterial", domain="heat_exchanger",
                   use_params_json=False)
    df = _load_csv("solution_data.csv")
    if df is None:
        raise RuntimeError("heat_multimaterial produced no solution_data.csv")
    _stash_csv("solution_data.csv", "heat_exchanger_solution.csv")
    _stash_csv("heat_multimaterial_kappa.csv", "heat_exchanger_kappa.csv")

    fig, axes = plt.subplots(1, 2, figsize=FIG_INCHES_TWOPANEL)
    # Left: kappa(x) as a scatter (we don't have the mesh, so use centroids).
    kdf = _load_csv("heat_multimaterial_kappa.csv")
    ax = axes[0]
    if kdf is not None:
        sc = ax.scatter(kdf["x"], kdf["y"], c=kdf["kappa"],
                        cmap="Greys", s=2, vmin=0, vmax=kdf["kappa"].max())
        ax.set_title(r"Conductivity $\kappa(x)$", fontsize=10)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

    # Right: temperature.
    sub = _final_frame(df)
    ax = axes[1]
    cs = _triplot(ax, sub["x"].values, sub["y"].values, sub["u"].values,
                  cmap="viridis", levels=16)
    ax.set_title("Temperature  $u(x)$", fontsize=10)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    fig.colorbar(cs, ax=ax, shrink=0.85)

    _savefig(fig, "heat_exchanger_solution")


# ---------------------------------------------------------------------------
#  Figure 2 — airfoil streamlines + thermal trail
#    FreeFEM doc: Fig. 3.5, p. 32
# ---------------------------------------------------------------------------
def fig_airfoil_streamlines_heat() -> None:
    # First run potential flow.
    run_simulation(pde="airfoil_potential_flow", domain="airfoil_naca0012",
                   use_params_json=False)
    psi = _load_csv("airfoil_psi.csv")
    _stash_csv("airfoil_psi.csv", "airfoil_psi.csv")
    # Then the convection-diffusion trail.
    run_simulation(pde="airfoil_thermal_trail", domain="airfoil_naca0012",
                   use_params_json=False)
    trail = _load_csv("solution_data.csv")
    if psi is None or trail is None:
        raise RuntimeError("airfoil run produced no CSVs")
    _stash_csv("solution_data.csv", "airfoil_trail.csv")

    fig, axes = plt.subplots(1, 2, figsize=FIG_INCHES_TWOPANEL)
    # Left: psi isolines (streamlines), zoom on the airfoil.
    # The mesh spans a R=5 far-field disk; clip to a slightly larger box
    # around the airfoil so the deflection is visible.
    ax = axes[0]
    psi_zoom = psi[(psi["x"] > -1.5) & (psi["x"] < 3.0)
                   & (psi["y"] > -1.5) & (psi["y"] < 1.5)]
    if len(psi_zoom) > 50:
        triang = mtri.Triangulation(psi_zoom["x"].values, psi_zoom["y"].values)
        ax.tricontour(triang, psi_zoom["psi"].values, levels=20,
                      colors="black", linewidths=0.4)
    ax.set_xlim(-1.0, 2.5)
    ax.set_ylim(-1.0, 1.0)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(r"Streamlines $\psi=\mathrm{const}$", fontsize=10)

    # Right: temperature at final time (also zoomed).
    ax = axes[1]
    sub = _final_frame(trail)
    sub_zoom = sub[(sub["x"] > -1.5) & (sub["x"] < 3.5)
                   & (sub["y"] > -1.5) & (sub["y"] < 1.5)]
    cs = _triplot(ax, sub_zoom["x"].values, sub_zoom["y"].values,
                  sub_zoom["u"].values, cmap="viridis", levels=18)
    ax.set_xlim(-1.0, 3.0)
    ax.set_ylim(-1.0, 1.0)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Thermal trail", fontsize=10)
    fig.colorbar(cs, ax=ax, shrink=0.85)

    _savefig(fig, "airfoil_streamlines_heat")


# ---------------------------------------------------------------------------
#  Figure 3 — rotating-hill CG vs DG
#    FreeFEM doc: Fig. 3.6, p. 33
# ---------------------------------------------------------------------------
def fig_rotating_hill_cg_vs_dg() -> None:
    run_simulation(pde="rotating_hill_cg", domain="disk",
                   use_params_json=False)
    cg = _load_csv("solution_data.csv")
    _stash_csv("solution_data.csv", "rotating_hill_cg.csv")
    run_simulation(pde="rotating_hill_dg", domain="disk",
                   use_params_json=False)
    dg = _load_csv("solution_data.csv")
    _stash_csv("solution_data.csv", "rotating_hill_dg.csv")
    if cg is None or dg is None:
        raise RuntimeError("rotating hill produced no CSVs")

    # Use SEPARATE color scales for CG and DG so that if one scheme blows up
    # numerically (e.g. DG instability at large dt) the other panel remains
    # readable. The two panels still use the same colormap (viridis) so the
    # qualitative comparison is fair.
    fig, axes = plt.subplots(1, 2, figsize=FIG_INCHES_TWOPANEL)
    last_cg = _final_frame(cg)
    last_dg = _final_frame(dg)

    for ax, sub, title in (
        (axes[0], last_cg, "CG (characteristics-Galerkin)"),
        (axes[1], last_dg, "DG (dual $P^1_{dc}$, upwind)"),
    ):
        triang = mtri.Triangulation(sub["x"].values, sub["y"].values)
        # Clip outliers to robust percentiles so the plot stays readable
        # even if the scheme is unstable.
        lo, hi = np.nanpercentile(sub["u"].values, [1, 99])
        cs = ax.tricontourf(triang, sub["u"].values, levels=18,
                            cmap="viridis", vmin=lo, vmax=hi)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title, fontsize=10)
        fig.colorbar(cs, ax=ax, shrink=0.85)

    _savefig(fig, "rotating_hill_cg_vs_dg")

    # Optional animated GIF for both schemes.
    try:
        _render_gif(cg, os.path.join(ANIM_DIR, "rotating_hill_cg.gif"),
                    title_fmt="CG  t = {:.2f}")
        _render_gif(dg, os.path.join(ANIM_DIR, "rotating_hill_dg.gif"),
                    title_fmt="DG  t = {:.2f}")
    except Exception as exc:  # noqa: BLE001
        print(f"  (GIF render skipped: {exc})")


# ---------------------------------------------------------------------------
#  Figure 4 — first 20 Dirichlet eigenmodes on the square
#    FreeFEM doc: Figs. 9.17-9.18, p. 236
# ---------------------------------------------------------------------------
def fig_dirichlet_eigenmodes_square() -> None:
    run_simulation(pde="dirichlet_eigenmodes", domain="square",
                   use_params_json=False)
    out = os.path.join(SPRIND_DIR, "dirichlet_eigenmodes_square.png")
    render_eigenmode_grid(out_path=out, n_modes=20)
    shutil.copyfile(out, os.path.join(FIGURES_DIR_PUBLIC,
                                      "dirichlet_eigenmodes_square.png"))
    _stash_csv("solution_data.csv", "dirichlet_eigenmodes_solution.csv")
    _stash_csv("eigenvalues.csv", "dirichlet_eigenmodes_eigenvalues.csv")


# ---------------------------------------------------------------------------
#  Figure 5 — Schwarz overlap convergence
#    FreeFEM doc: Fig. 9.25, p. 254
# ---------------------------------------------------------------------------
def fig_schwarz_overlap_convergence() -> None:
    run_simulation(pde="schwarz_overlap", domain="two_subdomains_overlap",
                   use_params_json=False)
    sol = _load_csv("solution_data.csv")
    conv = _load_csv("schwarz_convergence.csv")
    if sol is None or conv is None:
        raise RuntimeError("schwarz_overlap produced no CSVs")
    _stash_csv("solution_data.csv", "schwarz_overlap_solution.csv")
    _stash_csv("schwarz_convergence.csv", "schwarz_convergence.csv")

    # Wide figure with generous wspace; use a make_axes_locatable colorbar so
    # it sticks to the left panel and doesn't collide with the right panel's
    # y-axis labels.
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(10.5, 3.6),
                                   gridspec_kw={"wspace": 0.5})
    triang = mtri.Triangulation(sol["x"].values, sol["y"].values)
    cs = ax0.tricontourf(triang, sol["u"].values, levels=14, cmap="viridis")
    ax0.set_aspect("equal")
    ax0.set_xticks([])
    ax0.set_yticks([])
    ax0.set_title(r"$u$ on $\Omega_1$ (final iterate)", fontsize=10)
    divider = make_axes_locatable(ax0)
    cax = divider.append_axes("right", size="4%", pad=0.05)
    fig.colorbar(cs, cax=cax)

    ax1.semilogy(conv["iter"].values, conv["trace_mismatch_L2"].values,
                 marker="o", color="black", linewidth=1)
    ax1.set_xlabel("Schwarz iteration")
    ax1.set_ylabel(r"$\|u_1 - u_2\|_{L^2(\Omega_1)}$")
    ax1.set_title("Cross-mesh discrepancy", fontsize=10)
    ax1.grid(True, which="both", alpha=0.3)

    _savefig(fig, "schwarz_overlap_convergence")


# ---------------------------------------------------------------------------
#  Figure 6 — L-shape adapted mesh + solution
#    FreeFEM doc: Figs. 5.15-5.16, p. 105
# ---------------------------------------------------------------------------
def fig_lshape_corner_singularity() -> None:
    # We use the existing steady_heat PDE with f=1 on the lshape.
    run_simulation(pde="steady_heat", domain="lshape",
                   overrides={"Q": 1.0, "alpha": 1.0, "mesh_resolution": 60},
                   use_params_json=False)
    sol = _load_csv("solution_data.csv")
    if sol is None:
        raise RuntimeError("steady_heat on lshape produced no CSV")
    _stash_csv("solution_data.csv", "lshape_solution.csv")

    fig, axes = plt.subplots(1, 2, figsize=FIG_INCHES_TWOPANEL)
    # Left: mesh proxy via triangulation underlay.
    ax = axes[0]
    triang = mtri.Triangulation(sol["x"].values, sol["y"].values)
    ax.triplot(triang, color="black", linewidth=0.2)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("L-shape mesh", fontsize=10)

    # Right: solution isolines.
    ax = axes[1]
    cs = ax.tricontourf(triang, sol["u"].values, levels=18, cmap="viridis")
    ax.tricontour(triang, sol["u"].values, levels=18, colors="white",
                  linewidths=0.3)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Poisson solution", fontsize=10)
    fig.colorbar(cs, ax=ax, shrink=0.85)

    _savefig(fig, "lshape_corner_singularity")


# ---------------------------------------------------------------------------
#  Figure 7 — compressible Euler at Mach 2, half-disk
#    FreeFEM doc: Fig. 3.13, p. 53
# ---------------------------------------------------------------------------
def fig_compressible_euler_shock() -> None:
    run_simulation(pde="compressible_euler_shock", domain="half_disk_supersonic",
                   use_params_json=False)
    final = _load_csv("euler_final_fields.csv")
    if final is None:
        raise RuntimeError("compressible_euler_shock produced no CSV")
    _stash_csv("solution_data.csv", "euler_density_trajectory.csv")
    _stash_csv("euler_final_fields.csv", "euler_final_fields.csv")

    fig, ax = plt.subplots(figsize=FIG_INCHES_SINGLE)
    triang = mtri.Triangulation(final["x"].values, final["y"].values)
    cs = ax.tricontourf(triang, final["p"].values, levels=22, cmap="viridis")
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Pressure  $p(x)$  (Mach 2 inflow, half-disk)", fontsize=10)
    fig.colorbar(cs, ax=ax, shrink=0.85)

    _savefig(fig, "compressible_euler_shock")


# ---------------------------------------------------------------------------
#  GIF helper (rotating hill)
# ---------------------------------------------------------------------------
def _render_gif(df: pd.DataFrame, out_path: str, title_fmt: str,
                fps: int = 25, dur_seconds: float = 3.0):
    from matplotlib.animation import FuncAnimation, PillowWriter

    time_steps = sorted(df["time"].unique())
    if not time_steps:
        return
    target_frames = int(fps * dur_seconds)
    stride = max(1, len(time_steps) // target_frames)
    frames = time_steps[::stride]

    first = df[df["time"] == frames[0]]
    triang = mtri.Triangulation(first["x"].values, first["y"].values)
    umin, umax = df["u"].min(), df["u"].max()

    fig, ax = plt.subplots(figsize=(5, 4))

    def update(t):
        sub = df[df["time"] == t]
        ax.clear()
        ax.tricontourf(triang, sub["u"].values, levels=16,
                       cmap="viridis", vmin=umin, vmax=umax)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title_fmt.format(t), fontsize=10)

    anim = FuncAnimation(fig, update, frames=frames, interval=1000 // fps)
    anim.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)
    print(f"    GIF: {out_path}")


# ---------------------------------------------------------------------------
#  Public entry point
# ---------------------------------------------------------------------------
def generate_sprind_figure_pack() -> None:
    _ensure_dirs()

    steps = [
        ("heat-exchanger solution",          fig_heat_exchanger),
        ("airfoil streamlines + heat trail", fig_airfoil_streamlines_heat),
        ("rotating hill: CG vs DG",          fig_rotating_hill_cg_vs_dg),
        ("Dirichlet eigenmodes (square)",    fig_dirichlet_eigenmodes_square),
        ("Schwarz overlap convergence",      fig_schwarz_overlap_convergence),
        ("L-shape corner singularity",       fig_lshape_corner_singularity),
        ("Compressible Euler shock",         fig_compressible_euler_shock),
    ]

    for label, fn in steps:
        with _step(label):
            fn()

    _write_index_readme()
    print(f"\n[sprind] done. Figures in {SPRIND_DIR}")


def _write_index_readme() -> None:
    """Emit a small README cross-referencing each generated figure."""
    path = os.path.join(SPRIND_DIR, "README.md")
    with open(path, "w") as f:
        f.write(_README_TABLE)
    print(f"  index: {path}")


_README_TABLE = """\
# SPRIND figure pack

Auto-generated by `simulate --figures sprind`. Each figure is paired with the
SPRIND proposal section that uses it and the FreeFEM++ documentation figure
that it mirrors (Hecht et al., v3.20).

| PNG | SPRIND ref | FreeFEM doc ref | Regenerate |
|-----|------------|------------------|------------|
| `heat_exchanger_solution.png` | App. C.1.3 iii (multi-material steady heat) | Fig. 3.2, p. 25 | `simulate --pde heat_multimaterial --domain heat_exchanger` |
| `airfoil_streamlines_heat.png` | App. C.1.3 iv (convection + thermal trail) | Fig. 3.5, p. 32 | `simulate --pde airfoil_thermal_trail --domain airfoil_naca0012` |
| `rotating_hill_cg_vs_dg.png` | App. C.1.3 iv (rotating-hill benchmark) | Fig. 3.6, p. 33 | `simulate --pde rotating_hill_cg --domain disk` ; `simulate --pde rotating_hill_dg --domain disk` |
| `dirichlet_eigenmodes_square.png` | App. C.1.1 iv (Pillar 2 reference basis) | Figs. 9.17-9.18, p. 236 | `simulate --pde dirichlet_eigenmodes --domain square` |
| `schwarz_overlap_convergence.png` | App. C.1.5 iii (Pillar 3 motif) | Fig. 9.25, p. 254 | `simulate --pde schwarz_overlap --domain two_subdomains_overlap` |
| `lshape_corner_singularity.png` | App. C.1.3 iii (corner singularity) | Figs. 5.15-5.16, p. 105 | `simulate --pde steady_heat --domain lshape` |
| `compressible_euler_shock.png` | App. C.1.2 iii (shock pattern) | Fig. 3.13, p. 53 | `simulate --pde compressible_euler_shock --domain half_disk_supersonic` |

GIFs of the time-dependent cases (rotating hill CG/DG and airfoil thermal
trail) are written to `animations/`. They are not part of the LaTeX figure
pack but useful for the talk version.
"""


if __name__ == "__main__":
    generate_sprind_figure_pack()
