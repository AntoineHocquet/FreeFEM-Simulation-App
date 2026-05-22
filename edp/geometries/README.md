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
   `+ on(1, u = 0)` without per-geometry edits.

## Available geometries

| slug        | shape                                                              |
|-------------|--------------------------------------------------------------------|
| `disk`      | unit disk centered at the origin                                   |
| `square`    | unit square [0, 1]²                                                |
| `rectangle` | rectangle [0, 2] × [0, 1]                                          |
| `lshape`    | [0, 2]² minus [1, 2]² — re-entrant corner                          |
| `annulus`   | annulus with R_out = 1, R_in = 0.3                                 |

## Adding a new geometry

1. Drop `my_shape.idp` in this directory, honouring the interface above.
2. Append `"my_shape"` to the `GEOMETRIES` tuple in `src/simulate.py`.
3. (Optional) document it in this README and `edp/catalogue/README.md`.

That's it — any pluggable PDE can be solved on the new shape immediately.
