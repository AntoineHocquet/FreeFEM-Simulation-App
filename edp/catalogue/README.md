# Industrial-PDE Catalogue

Each entry in this directory is a FreeFEM++ template mirroring an entry from
Appendix **C.1** of the reference report ("PDEs by Industrial Application
Domain") and/or a figure in Hecht et al., *FreeFEM++ documentation* (v3.20).
The notation (T, v, α, Q, Γ_D, Γ_N, Pe, λ, μ, ν, ε(u), σ(u), …) matches the
report so the strong form, weak form, and the variables in the `.edp` line up
one-to-one.

Run any entry with:

```bash
simulate --pde <slug>            # use the catalogue default geometry
simulate --pde <slug> --domain <geom>   # pluggable scalar PDEs only
```

---

## Core PDE entries

| slug                  | report ref | strong form                                                | classification        |
|-----------------------|------------|------------------------------------------------------------|-----------------------|
| `advection_diffusion` | C.1.3 iv   | ∂T/∂t + v·∇T = ∇·(α∇T) + Q                                | parabolic; hyperbolic when Pe ≫ 1 |
| `heat`                | C.1.3 i    | ρc_p ∂T/∂t = ∇·(k∇T) + Q                                  | parabolic             |
| `steady_heat`         | C.1.3 iii  | −∇·(k∇T) = Q                                              | elliptic              |
| `eigenvalue`          | C.1.1 iv   | −Δu = λ u                                                 | elliptic eigenproblem |
| `stokes`              | C.1.2 iii  | −μ∇²v + ∇p = f,  ∇·v = 0                                  | elliptic saddle-point |
| `elasticity`          | C.1.1 i    | μ∇²u + (λ+μ)∇(∇·u) + f = 0                                | elliptic (static)     |

## SPRIND figure-pack PDEs

| slug                      | FreeFEM doc anchor      | what it computes                                                                 |
|---------------------------|-------------------------|----------------------------------------------------------------------------------|
| `heat_multimaterial`      | §3.2, Fig. 3.2 (p. 25)  | steady heat with piecewise κ on the heat-exchanger geometry                      |
| `airfoil_potential_flow`  | §3.5 (p. 31)            | Laplace of the stream-function ψ around a NACA0012 airfoil                       |
| `airfoil_thermal_trail`   | §3.5.1, Fig. 3.5 (p. 32)| convection-diffusion of a hot airfoil interior carried by the ψ-flow             |
| `rotating_hill_cg`        | §3.6, Fig. 3.6 (p. 33)  | pure convection of a Gaussian hill in `u = (y, -x)`, characteristics-Galerkin    |
| `rotating_hill_dg`        | §3.6, Fig. 3.6 (p. 33)  | same problem, dual-P1 discontinuous-Galerkin with upwind flux                    |
| `dirichlet_eigenmodes`    | §9.4, Figs. 9.17-9.18 (p. 236) | first 20 Dirichlet eigenmodes (shift-invert ARPACK)                       |
| `schwarz_overlap`         | §9.8.1, Fig. 9.25 (p. 254) | two-subdomain Schwarz iteration on overlapping rectangle ∪ disk               |
| `compressible_euler_shock`| §3.14, Fig. 3.13 (p. 53)   | Mach 2 inflow on a half-disk; characteristics-coupling shock-capture           |

Per-entry notes:

- **`advection_diffusion`** — the priority entry. Implicit Euler in time;
  residual-based **SUPG stabilization** keeps the scheme oscillation-free
  when the mesh Péclet number Pe_h = |v|·h / (2α) exceeds 1.
- **`stokes`** — Taylor-Hood P2/P1 (inf-sup stable). Geometry hardcoded.
- **`elasticity`** — 2D cantilever Lx = 4, Ly = 1 under gravity, clamped on
  the left edge.
- **`eigenvalue`** — first 6 Dirichlet–Laplace eigenpairs via ARPACK; the
  CSV uses the `time` column as the mode index.
- **`dirichlet_eigenmodes`** — same family as `eigenvalue` but extended to
  the first 20 modes plus a side-file `eigenvalues.csv` for the SPRIND
  figure pack.
- **`schwarz_overlap`** — uses the `two_subdomains_overlap` multi-mesh
  geometry; each Schwarz step solves a Dirichlet sub-problem with the
  neighbour's trace as boundary data.
- **`compressible_euler_shock`** — a reduced characteristics-coupling
  variant of the FreeFEM doc §3.14 example. Not a research-grade Euler
  solver; intended to produce the bow-shock-pattern figure the SPRIND
  proposal references.

---

## Geometry axis (`edp/geometries/`)

Scalar PDEs with `supports_domain = True` (everything in the catalogue
except `stokes` and `elasticity`) accept a `--domain` flag. See
`edp/geometries/README.md` for the full list — there are 13 geometries
covering plain shapes (disk, square, rectangle, lshape, annulus), smooth
non-convex (cardioid, cassini), the V-cut, multi-material
(`heat_exchanger`), the airfoil (`airfoil_naca0012`), the venturi-like
channel (`engine_section`), the two-subdomain Schwarz setup
(`two_subdomains_overlap`), and the supersonic half-disk
(`half_disk_supersonic`).

---

## Parameters

The dispatcher (`src/simulate.py`) merges three sources, in increasing
precedence:

```
catalogue defaults   <   params.json   <   CLI flags (--pde / --domain)
```

| key                | meaning                                                              |
|--------------------|----------------------------------------------------------------------|
| `pde`              | catalogue slug                                                       |
| `domain`           | geometry slug (pluggable scalar PDEs only)                           |
| `mesh_resolution`  | N — number of boundary segments                                      |
| `T`, `dt`          | final time T_end and time step Δt (time-dependent PDEs only)         |
| `alpha`            | α (diffusivity); μ for `stokes`; Young's modulus E for `elasticity`  |
| `Q`                | volumetric source; Poisson's ratio ν for `elasticity`                |
| `vx`, `vy`         | velocity components (advection_diffusion, airfoil_*)                 |

---

## Output schema

Every template writes `/workspace/data/solution_data.csv` with columns
`time, x, y, u`. For vector PDEs the `u` column is a scalar projection
(Stokes: `|v|`; elasticity: `|u|`); for the eigenvalue problems the `time`
column is reused as the mode index.

PDEs in the SPRIND figure pack also write side-files (e.g.
`heat_multimaterial_kappa.csv`, `airfoil_psi.csv`, `airfoil_velocity.csv`,
`schwarz_convergence.csv`, `euler_final_fields.csv`,
`eigenvalues.csv`). These are consumed by `src/sprind_figures.py` and are
documented in `data/sprind_figures/README.md` once the pack has been run.
