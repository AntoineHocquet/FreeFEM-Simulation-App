"""4x5 grid of the first 20 Dirichlet-Laplacian eigenmodes.

Mirrors FreeFEM doc Figs. 9.17-9.18 (p. 236).  Expects the CSVs
`data/solution_data.csv` (mode index in the `time` column) and
`data/eigenvalues.csv` (one row per mode) produced by the
`dirichlet_eigenmodes` PDE template.
"""

from __future__ import annotations

import os
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
import pandas as pd


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def render_eigenmode_grid(
    solution_csv: Optional[str] = None,
    eigenvalues_csv: Optional[str] = None,
    out_path: Optional[str] = None,
    n_modes: int = 20,
    nrows: int = 4,
    ncols: int = 5,
    figsize=(11, 9),
    dpi: int = 300,
):
    """Render the first ``n_modes`` eigenmodes on a single figure."""
    root = _project_root()
    solution_csv = solution_csv or os.path.join(root, "data", "solution_data.csv")
    eigenvalues_csv = eigenvalues_csv or os.path.join(root, "data", "eigenvalues.csv")
    out_path = out_path or os.path.join(
        root, "data", "sprind_figures", "dirichlet_eigenmodes_square.png"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    df = pd.read_csv(solution_csv)
    ev = pd.read_csv(eigenvalues_csv)

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    axes = np.asarray(axes).reshape(-1)
    modes_available = sorted(df["time"].unique())

    for i in range(nrows * ncols):
        ax = axes[i]
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
        if i >= n_modes or i >= len(modes_available):
            ax.set_visible(False)
            continue
        mode = modes_available[i]
        sub = df[df["time"] == mode]
        triang = mtri.Triangulation(sub["x"].values, sub["y"].values)
        amax = max(abs(sub["u"].min()), abs(sub["u"].max())) or 1.0
        ax.tricontourf(triang, sub["u"].values, levels=14,
                       cmap="coolwarm", vmin=-amax, vmax=amax)
        lam = ev.loc[ev["mode"] == int(mode), "lambda"]
        if not lam.empty:
            ax.set_title(rf"$\lambda_{{{i + 1}}}\!=\!{float(lam.iloc[0]):.2f}$",
                         fontsize=9)

    fig.suptitle("Dirichlet–Laplacian eigenmodes 1–20", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"Saved: {out_path}")
    return out_path


if __name__ == "__main__":
    render_eigenmode_grid()
