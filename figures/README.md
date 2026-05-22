# Figures (mirror of `data/sprind_figures/*.png`)

This directory is populated by `simulate --figures sprind` (see the top-level
README and `src/sprind_figures.py`). Each PNG mirrors the one in
`data/sprind_figures/`, with the same filename, so external repos (e.g. the
SPRIND proposal LaTeX source) can pull these by direct URL or as a git
submodule without having to know the FreeFEM pipeline's internals.

| PNG                                  | SPRIND ref                                       | FreeFEM doc anchor       |
|--------------------------------------|--------------------------------------------------|--------------------------|
| `heat_exchanger_solution.png`        | App. C.1.3 iii (multi-material steady heat)      | Fig. 3.2, p. 25          |
| `airfoil_streamlines_heat.png`       | App. C.1.3 iv (convection + thermal trail)       | Fig. 3.5, p. 32          |
| `rotating_hill_cg_vs_dg.png`         | App. C.1.3 iv (rotating-hill benchmark)          | Fig. 3.6, p. 33          |
| `dirichlet_eigenmodes_square.png`    | App. C.1.1 iv (Pillar 2 reference basis)         | Figs. 9.17-9.18, p. 236  |
| `schwarz_overlap_convergence.png`    | App. C.1.5 iii (Pillar 3 motif)                  | Fig. 9.25, p. 254        |
| `lshape_corner_singularity.png`      | App. C.1.3 iii (corner singularity)              | Figs. 5.15-5.16, p. 105  |
| `compressible_euler_shock.png`       | App. C.1.2 iii (shock pattern)                   | Fig. 3.13, p. 53         |

To regenerate from a clean checkout:

```bash
git clone https://github.com/AntoineHocquet/FreeFEM-Simulation-App.git
cd FreeFEM-Simulation-App
python3 -m venv venv && source venv/bin/activate
pip install -e .
simulate --figures sprind
```

Requires Docker (the dispatcher invokes the `antoinehocquet/freefem` v4.12
image). The eigenvalue solver requires FreeFEM to have ARPACK linked, which
the v4.12 image ships with — no extra `load "eigenvalue"` directive needed.
