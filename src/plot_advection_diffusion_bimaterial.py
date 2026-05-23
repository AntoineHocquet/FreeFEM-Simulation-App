#!/usr/bin/env python3
"""
Advection-diffusion on a bimaterial rectangle  Ω = Ω₁ ∪ Ω₂.

Strong form:
    ∂T/∂t + v·∇T = ∇·(α(x) ∇T)   in Ω × (0, T_end]
    α(x) = α₁  if x < x_Γ  (Ω₁, left  — faiblement diffusif)
    α(x) = α₂  if x ≥ x_Γ  (Ω₂, right — fortement diffusif)
    Neumann ∂T/∂n = 0 on Γ (zero-flux outer boundary)
    T(x, 0) = exp(-|x - x₀|² / (2σ²))    (Gaussienne amont)

Solved with explicit upwind-FD (advection) + conservative face-centred
diffusion (harmonic-mean α at bimaterial interface).

Output: data/advection_diffusion_bimaterial.png
         data/advection_diffusion_bimaterial.pdf
"""

import os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

# ── 1. DOMAIN ─────────────────────────────────────────────────────────────────
Lx, Ly = 3.0, 1.0
x_int  = 1.5                           # interface  Ω₁ | Ω₂  at x = x_int

Nx, Ny = 360, 120
x1d = np.linspace(0.0, Lx, Nx)
y1d = np.linspace(-Ly / 2.0, Ly / 2.0, Ny)
dx, dy = x1d[1] - x1d[0], y1d[1] - y1d[0]
X, Y = np.meshgrid(x1d, y1d)           # shape (Ny, Nx)

# ── 2. PHYSICAL PARAMETERS ───────────────────────────────────────────────────
vx     = 1.0                            # velocity [m/s], horizontal
alpha1 = 0.003                          # diffusivity in Ω₁  [m²/s]
alpha2 = 0.030                          # diffusivity in Ω₂  (10× contrast)
ALPHA  = np.where(X < x_int, alpha1, alpha2)

# Global Péclet numbers (L_char = half-domain = 1.5)
Lchar  = x_int
Pe1    = vx * Lchar / alpha1            # ≈ 500   (advection-dominated in Ω₁)
Pe2    = vx * Lchar / alpha2            # ≈  50   (diffusion significant in Ω₂)

# ── 3. TIME DISCRETISATION ────────────────────────────────────────────────────
Tend       = 2.0
safety     = 0.40
dt         = safety * min(dx / vx, dx**2 / (2.0 * alpha2))
nT         = int(Tend / dt) + 1
snap_times = [0.0, 0.80, 1.60]

# ── 4. INITIAL CONDITION ──────────────────────────────────────────────────────
x0, y0 = 0.35, 0.0                     # Gaussian centre (upstream of interface)
sigma  = 0.10                           # Gaussian half-width
T      = np.exp(-((X - x0)**2 + (Y - y0)**2) / (2.0 * sigma**2))

# ── 5. FINITE-DIFFERENCE SOLVER ───────────────────────────────────────────────

def div_alpha_grad(T, ALPHA, dx, dy):
    """
    Conservative discretisation of  ∇·(α∇T)  with:
      - harmonic-mean face coefficients  (essential for jump in α)
      - homogeneous Neumann on all boundaries
    """
    # --- x-direction
    a_xf = (2.0 * ALPHA[:, :-1] * ALPHA[:, 1:]
            / (ALPHA[:, :-1] + ALPHA[:, 1:] + 1e-30))
    fx   = a_xf * (T[:, 1:] - T[:, :-1]) / dx         # face flux (Ny, Nx-1)
    divx = np.zeros_like(T)
    divx[:, 1:-1] = (fx[:, 1:] - fx[:, :-1]) / dx     # interior
    divx[:,   0]  =  fx[:,   0] / dx                   # Neumann left
    divx[:,  -1]  = -fx[:,  -1] / dx                   # Neumann right

    # --- y-direction
    a_yf = (2.0 * ALPHA[:-1, :] * ALPHA[1:, :]
            / (ALPHA[:-1, :] + ALPHA[1:, :] + 1e-30))
    fy   = a_yf * (T[1:, :] - T[:-1, :]) / dy         # face flux (Ny-1, Nx)
    divy = np.zeros_like(T)
    divy[1:-1, :] = (fy[1:, :] - fy[:-1, :]) / dy
    divy[  0, :]  =  fy[  0, :] / dy                  # Neumann bottom
    divy[ -1, :]  = -fy[ -1, :] / dy                  # Neumann top

    return divx + divy


snapshots    = {0.0: T.copy()}
snap_done    = {ts: (ts == 0.0) for ts in snap_times}
t            = 0.0

for _ in range(nT):
    # upwind advection  (vx > 0  →  backward difference)
    adv        = np.zeros_like(T)
    adv[:, 1:] = vx * (T[:, 1:] - T[:, :-1]) / dx
    adv[:,  0] = vx * T[:,  0] / dx              # inflow: ambient = 0

    T = T + dt * (-adv + div_alpha_grad(T, ALPHA, dx, dy))
    T = np.clip(T, 0.0, None)
    t += dt

    for ts in snap_times:
        if not snap_done[ts] and t >= ts:
            snapshots[ts] = T.copy()
            snap_done[ts] = True

# ── 6. FIGURE ─────────────────────────────────────────────────────────────────
mpl.rcParams.update({
    "font.family":     "DejaVu Sans",
    "mathtext.fontset": "dejavusans",
    "axes.linewidth":  1.6,
})

fig, axes = plt.subplots(
    1, 3,
    figsize=(15.0, 4.4),
    gridspec_kw={"wspace": 0.04},
)
fig.patch.set_facecolor("white")
plt.subplots_adjust(left=0.06, right=0.88, bottom=0.16, top=0.80)

vmax  = float(snapshots[0.0].max())
norm  = mpl.colors.Normalize(vmin=0.0, vmax=vmax)
cmap  = mpl.cm.plasma

# stroke helper for readable labels on any background
def stroke(lw=2.5, fg="black"):
    return [pe.withStroke(linewidth=lw, foreground=fg)]

for idx, (ax, ts) in enumerate(zip(axes, snap_times)):
    snap = snapshots[ts]

    # ── temperature field (gouraud = smooth bilinear interpolation) ──────────
    ax.pcolormesh(X, Y, snap, cmap=cmap, norm=norm,
                  shading="gouraud", rasterized=True, zorder=1)

    # ── white iso-contours ───────────────────────────────────────────────────
    levels = np.linspace(0.08 * vmax, 0.92 * vmax, 7)
    ax.contour(X, Y, snap, levels=levels,
               colors="white", linewidths=0.7, alpha=0.50, zorder=2)

    # ── sub-domain boundary (interface) ─────────────────────────────────────
    ax.axvline(x_int, color="white", ls="--", lw=1.8, alpha=0.90, zorder=3)

    # ── outer boundary annotation Γ  (first panel only) ─────────────────────
    if idx == 0:
        ax.text(
            0.04, 0.50, r"$\Gamma$",
            transform=ax.transAxes, fontsize=13,
            color="#1a1a1a", va="center", ha="center",
            path_effects=stroke(3.0, "white"),
        )

    # ── Ω₁  label ────────────────────────────────────────────────────────────
    ax.text(
        x_int / 2.0, 0.38,
        r"$\Omega_1$",
        fontsize=15, fontweight="bold",
        color="white", va="center", ha="center",
        path_effects=stroke(3.5, "#00000088"),
        zorder=5,
    )

    # ── Ω₂  label ────────────────────────────────────────────────────────────
    ax.text(
        (Lx + x_int) / 2.0, 0.38,
        r"$\Omega_2$",
        fontsize=15, fontweight="bold",
        color="white", va="center", ha="center",
        path_effects=stroke(3.5, "#00000088"),
        zorder=5,
    )

    # ── velocity arrow ────────────────────────────────────────────────────────
    ax.annotate(
        "", xy=(2.62, -0.41), xytext=(2.15, -0.41),
        arrowprops=dict(arrowstyle="-|>", color="white",
                        lw=1.8, mutation_scale=12),
        zorder=6,
    )
    ax.text(2.39, -0.35, r"$\mathbf{v}$",
            ha="center", fontsize=10, color="white",
            path_effects=stroke(2.5, "#00000088"), zorder=6)

    # ── time stamp ────────────────────────────────────────────────────────────
    ax.set_title(f"$t = {ts:.2f}$ s", fontsize=12, pad=6, color="#111111")

    # ── axes formatting ───────────────────────────────────────────────────────
    ax.set_xlim(0.0, Lx)
    ax.set_ylim(-Ly / 2.0, Ly / 2.0)
    ax.set_xlabel("$x$  (m)", fontsize=10, labelpad=4)
    ax.set_xticks([0.0, 0.75, 1.5, 2.25, 3.0])
    ax.set_xticklabels(["0", "0.75", "1.5", "2.25", "3"], fontsize=8)
    ax.set_yticks([-0.5, 0.0, 0.5])
    if idx == 0:
        ax.set_ylabel("$y$  (m)", fontsize=10, labelpad=4)
        ax.set_yticklabels([r"$-0.5$", "$0$", r"$+0.5$"], fontsize=9)
    else:
        ax.set_yticklabels([])

    for sp in ax.spines.values():
        sp.set_linewidth(1.8)
        sp.set_color("#333333")

# ── shared colorbar ───────────────────────────────────────────────────────────
cax  = fig.add_axes([0.895, 0.16, 0.018, 0.64])
cbar = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax)
cbar.set_label("$T$  (u.a.)", fontsize=11, labelpad=6)
cbar.ax.tick_params(labelsize=9)

# ── diffusivity legend (bottom strip) ────────────────────────────────────────
fig.patches.extend([
    mpl.patches.FancyBboxPatch(
        (0.065, 0.01), 0.38, 0.11,
        boxstyle="round,pad=0.01", linewidth=0.8,
        edgecolor="#3B82F6", facecolor="#EFF6FF", transform=fig.transFigure,
        zorder=0,
    ),
    mpl.patches.FancyBboxPatch(
        (0.50, 0.01), 0.38, 0.11,
        boxstyle="round,pad=0.01", linewidth=0.8,
        edgecolor="#F97316", facecolor="#FFF7ED", transform=fig.transFigure,
        zorder=0,
    ),
])
fig.text(0.255, 0.065,
         r"$\Omega_1$:  $\alpha_1 = 0.003\;\mathrm{m^2\!/s}$"
         f"  —  Pe$_1 \\approx {Pe1:g}$  (advection dominante)",
         ha="center", fontsize=9.5, color="#1D4ED8", fontweight="bold")
fig.text(0.690, 0.065,
         r"$\Omega_2$:  $\alpha_2 = 0.030\;\mathrm{m^2\!/s}$"
         f"  —  Pe$_2 \\approx {Pe2:g}$  (diffusion significative)",
         ha="center", fontsize=9.5, color="#C2410C", fontweight="bold")

# ── suptitle ──────────────────────────────────────────────────────────────────
fig.suptitle(
    r"Advection-diffusion sur un domaine bi-matériau  "
    r"$\Omega = \Omega_1 \cup \Omega_2$,  $\partial\Omega = \Gamma$"
    "\n"
    r"$\partial_t T + \mathbf{v}\!\cdot\!\nabla T "
    r"= \nabla\!\cdot\!(\alpha(\mathbf{x})\,\nabla T)$"
    r"$\quad\mathbf{v} = (1,\,0)$"
    r"$\quad T_0 = \mathcal{G}_{\sigma=0.1}(x\!-\!0.35,\,y)$",
    fontsize=11.5,
    y=0.975,
    color="#111111",
)

# ── save ──────────────────────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
out_base = "data/advection_diffusion_bimaterial"
fig.savefig(out_base + ".png", dpi=200, bbox_inches="tight", facecolor="white")
fig.savefig(out_base + ".pdf", bbox_inches="tight", facecolor="white")
print(f"Saved  {out_base}.png  (200 dpi)")
print(f"Saved  {out_base}.pdf")
plt.close(fig)
