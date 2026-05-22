# Geometry templates

Each `.idp` file in this directory defines a 2D domain that can be plugged
into any scalar-PDE template from `edp/catalogue/`. They are pulled in by
the line

```edp
int N = %%mesh_resolution%%;
include "/workspace/edp/geometries/%%domain%%.idp"
```

emitted by `src/simulate.py` when it generates the final `.edp`.

## Interface

A geometry file must:

1. Use the variable `N` (defined by the caller) as the mesh-resolution input.
2. Declare a `mesh Th` triangulation.
3. Export the names below so PDE templates can reuse them:

| name      | type   | meaning                                              |
|-----------|--------|------------------------------------------------------|
| `Th`      | `mesh` | the triangulation                                    |
| `Lchar`   | `real` | characteristic length (used in Péclet diagnostics)   |
| `xc, yc`  | `real` | a sensible center point (for initial conditions)     |

4. Label the entire boundary `1` so PDE templates can apply Γ_D with
   `+ on(1, u = 0)` without per-geometry edits. (Geometries with extra
   internal labels are noted below.)

## Available geometries

### Plain single-mesh, pluggable into any scalar PDE

| slug        | shape                                                              |
|-------------|--------------------------------------------------------------------|
| `disk`      | unit disk centered at the origin                                   |
| `square`    | unit square [0, 1]²                                                |
| `rectangle` | rectangle [0, 2] × [0, 1]                                          |
| `lshape`    | [0, 2]² minus [1, 2]² — re-entrant corner                          |
| `annulus`   | annulus with R_out = 1, R_in = 0.3                                 |
| `cardioid`  | epicycloid for `a = b = 1`; smooth non-convex (FreeFEM doc §5.9)   |
| `cassini`   | peanut-shaped `(2 cos 2t + 3)(cos t, sin t)` (FreeFEM doc §5.10)   |
| `v_cut`     | unit disk with a sector removed; controllable opening angle        |

### Multi-label or PDE-paired geometries

| slug                      | what                                                      | paired with                  |
|---------------------------|-----------------------------------------------------------|------------------------------|
| `heat_exchanger`          | disk R=5 + two embedded rectangular conductors (labels 1, 2, 3) | `heat_multimaterial`   |
| `airfoil_naca0012`        | NACA0012 in a R=5 far-field disk (labels 1 = far-field, 2 = airfoil) | `airfoil_potential_flow`, `airfoil_thermal_trail` |
| `engine_section`          | venturi-like channel with a smooth bump on the lower wall | any Stokes-like flow setup    |
| `two_subdomains_overlap`  | rectangle Ω₁ ∪ disk Ω₂ with non-empty overlap; exports TWO meshes (`TH`, `th`) and an alias `Th = TH` for compatibility | `schwarz_overlap`     |
| `half_disk_supersonic`    | open rectangle with a half-disk obstacle and four labelled boundaries | `compressible_euler_shock` |

Geometries marked "paired with" carry a `pde_locked` flag in
`src/simulate.py`. They are still selectable from the CLI for any PDE, but
the dispatcher prints a warning when the pairing is broken.

## Adding a new geometry

1. Drop `my_shape.idp` in this directory, honouring the interface above.
2. Append `"my_shape"` to the `GEOMETRIES` tuple in `src/simulate.py`. If
   the geometry only makes sense with a specific PDE, also add an entry to
   `GEOMETRY_META` (`{"pde_locked": "my_pde"}` or `{"multi_mesh": True}`).
3. (Optional) document it in this README and `edp/catalogue/README.md`.

That's it — any pluggable PDE can be solved on the new shape immediately.
