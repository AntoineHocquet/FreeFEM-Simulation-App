# FreeFEM Simulation App

A Dockerized FEM simulation pipeline for industrial PDEs, driven from Python.
Pick a PDE, pick a domain shape, run a single command, get plots and animated
GIFs. No local FreeFEM++ install needed — everything runs inside a public
Docker image.

> **Built for:** quick demos and reproducible numerical experiments on the
> canonical PDEs that show up in heat transfer, fluid dynamics, structural
> mechanics, and modal analysis. Notation follows Appendix C.1 of the
> reference report — strong form, weak form, and the FreeFEM `.edp` line up
> one-to-one.

---

## Highlights

- **Catalogue of 6 industrial PDEs** (`edp/catalogue/`): advection-diffusion
  (with SUPG), heat / Poisson, Stokes (Taylor-Hood P2/P1), linear elasticity,
  scalar Laplacian eigenvalue. See `edp/catalogue/README.md`.
- **5 pluggable geometries** (`edp/geometries/`): disk, square, rectangle,
  L-shape (re-entrant corner), annulus. Any scalar PDE solves on any shape.
- **One CLI**: `simulate --pde <slug> --domain <slug>`. Outputs CSV, static
  PNG, and animated GIF under `data/`.
- **Bring-your-own FreeFEM not required.** The dispatcher invokes the public
  image `antoinehocquet/freefem` (FreeFEM++ v4.12) with the project root
  mounted at `/workspace`.
- **Bonus**: a Landau–Lifshitz–Gilbert (LLG) magnetisation simulation with
  its own visualiser (`simulate --run llg`).

---

## Quick start

```bash
git clone https://github.com/AntoineHocquet/FreeFEM-Simulation-App.git
cd FreeFEM-Simulation-App
python3 -m venv venv && source venv/bin/activate
pip install -e .

# Run the default pipeline (advection-diffusion on the unit disk) and produce
# the static plot + the animated GIF in data/.
simulate --run all
```

Requirements: **Python 3.8+**, **Docker** (the daemon must be running and
your user must be able to `docker run` — typically `sudo usermod -aG docker
$USER` followed by a re-login).

---

## CLI reference

```bash
simulate [--run <stage>] [--pde <slug>] [--domain <slug>]
```

| `--run` value | what it does                                                    |
|---------------|-----------------------------------------------------------------|
| `all`         | sim → viz → gif (the default)                                   |
| `sim`         | run the FreeFEM solver in Docker, write `data/solution_data.csv`|
| `viz`         | render the final time step → `data/heat_final.png`              |
| `gif`         | render the full animation → `data/heat_equation_simulation.gif` |
| `list`        | print the PDE / geometry catalogue                              |
| `llg`         | run the LLG example, write step-by-step CSVs to `data/data_llg/`|
| `llg-gif`     | turn the LLG CSVs into `data/llg_magnetization.gif`             |

`--pde` and `--domain` select an entry from the catalogue and override
anything in `params.json` for that run.

```bash
# A few representative invocations
simulate --pde advection_diffusion --domain lshape
simulate --pde steady_heat         --domain annulus
simulate --pde eigenvalue          --domain square
simulate --pde stokes                              # geometry is hardcoded
simulate --run list                                # see everything available
```

---

## Configuration (`params.json`)

The dispatcher merges three sources, in increasing precedence:

```
   catalogue defaults   <   params.json   <   CLI flags (--pde / --domain)
```

`params.json` ships with sensible advection-diffusion defaults:

```json
{
  "pde": "advection_diffusion",
  "domain": "disk",
  "T": 2.0,
  "dt": 0.02,
  "mesh_resolution": 80,
  "alpha": 0.005,
  "vx": 1.0,
  "vy": 0.0,
  "Q": 0.0
}
```

| key               | meaning                                                                  |
|-------------------|--------------------------------------------------------------------------|
| `pde`             | catalogue slug — see `edp/catalogue/README.md`                           |
| `domain`          | geometry slug (`disk`, `square`, `rectangle`, `lshape`, `annulus`)       |
| `mesh_resolution` | N = number of boundary segments                                          |
| `T`, `dt`         | final time T_end and time step Δt (time-dependent PDEs only)             |
| `alpha`           | α (diffusivity); μ for `stokes`; Young's modulus E for `elasticity`      |
| `Q`               | volumetric source; Poisson's ratio ν for `elasticity`                    |
| `vx`, `vy`        | velocity components (advection_diffusion only)                           |

---

## Catalogue at a glance

| PDE slug              | report ref | strong form                                            | geometry  |
|-----------------------|------------|--------------------------------------------------------|-----------|
| `advection_diffusion` | C.1.3 iv   | ∂T/∂t + v·∇T = ∇·(α∇T) + Q  *(with SUPG stabilization)* | pluggable |
| `heat`                | C.1.3 i    | ρc_p ∂T/∂t = ∇·(k∇T) + Q                               | pluggable |
| `steady_heat`         | C.1.3 iii  | −∇·(k∇T) = Q                                           | pluggable |
| `eigenvalue`          | C.1.1 iv   | −Δu = λ u  *(first 6 modes)*                           | pluggable |
| `stokes`              | C.1.2 iii  | −μ∇²v + ∇p = f, ∇·v = 0  *(Taylor-Hood P2/P1)*         | hardcoded |
| `elasticity`          | C.1.1 i    | μ∇²u + (λ+μ)∇(∇·u) + f = 0                             | hardcoded |

| domain slug | shape                                                            |
|-------------|------------------------------------------------------------------|
| `disk`      | unit disk centered at the origin                                 |
| `square`    | unit square [0, 1]²                                              |
| `rectangle` | rectangle [0, 2] × [0, 1]                                        |
| `lshape`    | [0, 2]² minus [1, 2]² — classic re-entrant-corner test case      |
| `annulus`   | annulus with R_out = 1, R_in = 0.3                               |

Stokes and elasticity intentionally keep their own geometries — their
boundary labels encode the BC pattern (inflow vs. no-slip; clamped vs.
traction). Full details in `edp/catalogue/README.md`.

---

## How it fits together

```
.
├── src/                        Python pipeline
│   ├── main.py                 argparse CLI ("simulate" entry point)
│   ├── simulate.py             catalogue registry + Docker dispatcher
│   ├── config.py               params.json loader
│   ├── visualize.py            final-frame PNG renderer
│   ├── visualize_gif.py        animated GIF renderer (heat-style)
│   └── visualize_llg*.py       LLG vector-field viz
│
├── edp/
│   ├── catalogue/              one .edp template per PDE
│   │   └── *_template.edp      placeholders %%T%%, %%dt%%, %%alpha%%, …
│   ├── geometries/             pluggable mesh definitions
│   │   └── *.idp               exports mesh Th, Lchar, (xc, yc)
│   └── initsllg.edp            LLG example
│
├── docker/                     Dockerfile (if you want to rebuild the image)
├── params.json                 user-editable defaults
├── tests/test_pipeline.py      end-to-end smoke test (csv + gif exist)
└── data/                       all generated outputs land here (gitignored)
```

**Inside the container**, the project root is mounted at `/workspace`. Every
`.edp` reads from `/workspace/edp/...` and writes to `/workspace/data/...`,
so generated files end up in `data/` on the host.

**Template substitution.** Each `<pde>_template.edp` contains `%%key%%`
placeholders. `simulate.py` merges defaults + `params.json` + CLI flags and
performs a literal `%%key%% → value` substitution before the Docker run.
Geometries are pulled in via FreeFEM's `include` directive:

```edp
int N = %%mesh_resolution%%;
include "/workspace/edp/geometries/%%domain%%.idp"   // -> mesh Th, Lchar, (xc, yc)
```

**Output schema.** Every scalar PDE writes `data/solution_data.csv` with
columns `time,x,y,u`. For vector PDEs the `u` column is a scalar projection
(`|v|` for Stokes, `|u|` for elasticity); for the eigenvalue problem the
`time` column is reused as the mode index.

---

## Extending the catalogue

**Add a PDE.** Drop `<slug>_template.edp` into `edp/catalogue/`, then register
it in the `CATALOGUE` dict of `src/simulate.py`:

```python
"my_pde": {
    "template": "my_pde_template.edp",
    "label": "My PDE",
    "supports_domain": True,           # accept --domain ?
    "default_domain": "disk",
    "defaults": {"T": 1.0, "dt": 0.01, "mesh_resolution": 60, ...},
},
```

For a `supports_domain=True` PDE, the template should `include
"/workspace/edp/geometries/%%domain%%.idp"` and treat label `1` as Γ_D.

**Add a geometry.** Create `edp/geometries/<slug>.idp` that defines
`mesh Th`, `real Lchar`, and `real xc, yc`, with label `1` on the Dirichlet
boundary. Then append the slug to the `GEOMETRIES` tuple in
`src/simulate.py`.

---

## Tests

```bash
pytest tests/
```

The smoke test runs the default pipeline (`simulate --run all`) and asserts
that `data/solution_data.csv` and `data/heat_equation_simulation.gif` exist
and are non-empty.

---

## Dependencies

| | |
|---|---|
| Python | 3.8 or newer |
| Docker | daemon running, current user in the `docker` group |
| FreeFEM++ | not required locally — pulled in via `antoinehocquet/freefem` (v4.12) |
| Python packages | `pandas`, `matplotlib`, `numpy` (installed by `pip install -e .`) |

The Docker image is based on the [official FreeFEM build][freefem-docker]
(v4.12, December 2022). To rebuild it yourself: `cd docker && ./build.sh`.

[freefem-docker]: https://github.com/FreeFem/FreeFem-docker
