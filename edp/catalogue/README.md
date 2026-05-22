# Industrial-PDE Catalogue

This catalogue mirrors Appendix **C.1** of the report ("PDEs by Industrial
Application Domain"). Each entry is a FreeFEM++ template that can be driven
from the Python CLI with

```bash
simulate --run sim --pde <name>
```

The notation (T, v, α, Q, Γ_D, Γ_N, Pe, λ, μ, ν, ε(u), σ(u), …) matches the
report so the strong form, weak form and the variables in the `.edp` line up
one-to-one.

| slug                  | Report ref     | Strong form                                                              | Geometry / BCs                                         |
|-----------------------|----------------|--------------------------------------------------------------------------|--------------------------------------------------------|
| `advection_diffusion` | C.1.3 iv       | ∂T/∂t + v·∇T = ∇·(α∇T) + Q                                              | unit disk; T = 0 on Γ_D = ∂Ω; SUPG stabilization      |
| `heat`                | C.1.3 i        | ρc_p ∂T/∂t = ∇·(k∇T) + Q                                                | unit disk; T = 0 on Γ_D                               |
| `steady_heat`         | C.1.3 iii      | −∇·(k∇T) = Q                                                            | unit disk; T = 0 on Γ_D                               |
| `stokes`              | C.1.2 iii      | −μ∇²v + ∇p = f, ∇·v = 0                                                 | unit disk; v=(1,0) on upper arc, no-slip on lower arc |
| `elasticity`          | C.1.1 i        | μ∇²u + (λ+μ)∇(∇·u) + f = 0                                              | cantilever Lx=4, Ly=1; u = 0 on left, gravity load    |
| `eigenvalue`          | C.1.1 iv       | −Δu = λ u                                                               | unit disk; u = 0 on ∂Ω; first 6 modes reported        |

### Parameters

The dispatcher (`src/simulate.py`) merges three sources, in increasing
precedence: per-PDE defaults  →  `params.json`  →  CLI flags.

Shared keys:

| key                | meaning                                                       |
|--------------------|---------------------------------------------------------------|
| `pde`              | catalogue slug (any of the table above)                       |
| `mesh_resolution`  | number of boundary segments N                                 |
| `T`, `dt`          | final time T_end and time step Δt (time-dependent PDEs only)  |
| `alpha`            | α (diffusivity); μ for `stokes`; E (Young's modulus) for `elasticity` |
| `Q`                | volumetric source; ν (Poisson's ratio) for `elasticity`       |
| `vx`, `vy`         | velocity components (advection_diffusion only)                |

### Priority entry: Advection-Diffusion

`advection_diffusion_template.edp` implements implicit Euler in time and a
**residual-based SUPG stabilization** so the scheme stays oscillation-free
when the mesh Péclet number Pe_h = |v|h/(2α) exceeds 1 — the regime the
report flags as the "numerical challenge" for standard Galerkin FEM.
The stabilization parameter follows the doubly-asymptotic rule

    τ_K = h_K / (2 |v|) · ξ(Pe_h),    ξ(Pe_h) ≈ min(Pe_h / 3, 1),

and the script prints the global Péclet number, h_max, Pe_h and τ_SUPG at
start-up.

### Output schema

Every template writes `/workspace/data/solution_data.csv` with columns
`time,x,y,u` so the existing `src/visualize.py` and `src/visualize_gif.py`
pipelines work unchanged. For vector PDEs the `u` column is a scalar
projection (Stokes: speed |v|; elasticity: displacement magnitude |u|;
eigenvalue: the eigenfunction value, with `time` reused as the mode index).
