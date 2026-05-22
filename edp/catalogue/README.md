# Industrial-PDE Catalogue

Each entry in this directory is a FreeFEM++ template mirroring an entry from
Appendix **C.1** of the reference report ("PDEs by Industrial Application
Domain"). The notation
(T, v, α, Q, Γ_D, Γ_N, Pe, λ, μ, ν, ε(u), σ(u), …) matches the report so
the strong form, weak form, and the variables in the `.edp` line up
one-to-one.

Run any entry with:

```bash
simulate --pde <slug>            # use the catalogue default geometry
simulate --pde <slug> --domain <geom>   # pluggable scalar PDEs only
```

---

## PDE entries

| slug                  | report ref | strong form                                                | classification        |
|-----------------------|------------|------------------------------------------------------------|-----------------------|
| `advection_diffusion` | C.1.3 iv   | ∂T/∂t + v·∇T = ∇·(α∇T) + Q                                | parabolic; hyperbolic when Pe ≫ 1 |
| `heat`                | C.1.3 i    | ρc_p ∂T/∂t = ∇·(k∇T) + Q                                  | parabolic             |
| `steady_heat`         | C.1.3 iii  | −∇·(k∇T) = Q                                              | elliptic              |
| `eigenvalue`          | C.1.1 iv   | −Δu = λ u                                                 | elliptic eigenproblem |
| `stokes`              | C.1.2 iii  | −μ∇²v + ∇p = f,  ∇·v = 0                                  | elliptic saddle-point |
| `elasticity`          | C.1.1 i    | μ∇²u + (λ+μ)∇(∇·u) + f = 0                                | elliptic (static)     |

Per-entry notes:

- **`advection_diffusion`** — the priority entry. Implicit Euler in time;
  residual-based **SUPG stabilization** keeps the scheme oscillation-free
  when the mesh Péclet number Pe_h = |v|·h / (2α) exceeds 1 (the regime the
  report flags as the numerical challenge for plain Galerkin FEM). The
  stabilisation parameter follows the doubly-asymptotic rule
  τ_K = h_K / (2|v|) · ξ(Pe_h),  ξ(Pe_h) ≈ min(Pe_h / 3, 1). The script
  prints Pe, h_max, Pe_h, and τ_SUPG at start-up.
- **`stokes`** — Taylor-Hood P2/P1 (inf-sup stable). Geometry hardcoded
  (unit disk, v = (1, 0) on the upper arc, no-slip on the lower arc) because
  the boundary labels encode the BC pattern.
- **`elasticity`** — 2D cantilever Lx = 4, Ly = 1 under gravity, clamped on
  the left edge. Stress σ = λ tr(ε) I + 2μ ε(u); `alpha`/`Q` are reused as
  Young's modulus E and Poisson's ratio ν.
- **`eigenvalue`** — first 6 Dirichlet–Laplace eigenpairs via ARPACK; the
  CSV uses the `time` column as the mode index.

---

## Geometry axis (`edp/geometries/`)

Scalar PDEs with `supports_domain = True` (advection_diffusion, heat,
steady_heat, eigenvalue) accept a `--domain` flag. Each geometry `.idp` file
exports `mesh Th`, a characteristic length `Lchar`, and a center point
`(xc, yc)`, and labels the entire boundary `1` so it reads as Γ_D in the
variational problem.

| slug        | shape                                                              |
|-------------|--------------------------------------------------------------------|
| `disk`      | unit disk centered at the origin                                   |
| `square`    | unit square [0, 1]²                                                |
| `rectangle` | rectangle [0, 2] × [0, 1]                                          |
| `lshape`    | [0, 2]² minus [1, 2]² — classic re-entrant-corner test case        |
| `annulus`   | annulus with R_out = 1, R_in = 0.3 (hole carved by CW inner border)|

Stokes and elasticity intentionally keep their own geometries because their
boundary-label conventions encode the BC pattern (inflow vs. no-slip;
clamped vs. traction).

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
| `vx`, `vy`         | velocity components (advection_diffusion only)                       |

---

## Output schema

Every template writes `/workspace/data/solution_data.csv` with columns
`time, x, y, u`. For vector PDEs the `u` column is a scalar projection
(Stokes: `|v|`; elasticity: `|u|`); for the eigenvalue problem the `time`
column is reused as the mode index. This keeps `src/visualize.py` and
`src/visualize_gif.py` working unchanged across the whole catalogue.
