# src/simulate.py
import subprocess
import os
import platform
from config import load_config


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDP_DIR = os.path.join(PROJECT_ROOT, "edp")
CATALOGUE_DIR = os.path.join(EDP_DIR, "catalogue")
GEOMETRIES_DIR = os.path.join(EDP_DIR, "geometries")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


# ---------------------------------------------------------------------------
#  Catalogue of industrial PDEs (notation follows the report appendix C.1.x).
#  Each entry maps a short slug -> (template file, default parameters, label,
#  geometry support flag). Parameter names match the symbols of the report:
#      alpha — diffusivity (or Young's modulus E for elasticity)
#      Q     — volumetric source (or Poisson's ratio nu for elasticity)
#      vx/vy — velocity components (advection_diffusion only)
#      T     — final time T_end (time horizon, *not* the unknown temperature)
#      dt    — time step Delta t
#      mesh_resolution — N points along the boundary
#
#  The "domain" axis (GEOMETRIES below) plugs pre-made meshes into any PDE
#  that opts in via supports_domain=True. See edp/geometries/README.md.
#
#  Geometry registration entries may carry:
#      "multi_mesh": True   -> the .idp exports more than one mesh (e.g.
#                              two_subdomains_overlap exports TH and th); the
#                              dispatcher does no special handling beyond not
#                              complaining about it -- the PDE template knows
#                              the convention.
#      "pde_locked": <slug> -> this geometry is meaningful only with that PDE
#                              (e.g. half_disk_supersonic + Euler).
# ---------------------------------------------------------------------------

# Geometries available as the "domain" axis (edp/geometries/<name>.idp).
# Order is conventional only; not all PDEs accept every geometry.
GEOMETRIES = (
    "disk", "square", "rectangle", "lshape", "annulus",
    "heat_exchanger", "airfoil_naca0012", "cardioid", "cassini",
    "engine_section", "v_cut", "two_subdomains_overlap",
    "half_disk_supersonic", "bimaterial_rectangle", "aquifer_lens",
)

# Per-geometry metadata for the dispatcher.  Geometries not listed here use
# the single-mesh, PDE-agnostic default.
GEOMETRY_META = {
    "two_subdomains_overlap": {"multi_mesh": True, "pde_locked": "schwarz_overlap"},
    "heat_exchanger":         {"pde_locked": "heat_multimaterial"},
    "airfoil_naca0012":       {"pde_locked": None},   # used by 2 PDEs
    "half_disk_supersonic":   {"pde_locked": "compressible_euler_shock"},
    "bimaterial_rectangle":   {"pde_locked": "advection_diffusion_bimaterial"},
    "aquifer_lens":            {"pde_locked": "advection_diffusion_aquifer"},
}

CATALOGUE = {
    "advection_diffusion": {
        "template": "advection_diffusion_template.edp",
        "label": "Advection-Diffusion (C.1.3 iv)",
        "supports_domain": True,
        "default_domain": "disk",
        "defaults": {
            "T": 2.0, "dt": 0.02, "mesh_resolution": 80,
            "alpha": 0.005, "vx": 1.0, "vy": 0.0, "Q": 0.0,
        },
    },
    "advection_diffusion_bimaterial": {
        "template": "advection_diffusion_bimaterial_template.edp",
        "label": "Advection-Diffusion Bi-matériau Ω₁∪Ω₂ (C.1.3 iv ext.)",
        "supports_domain": False,
        "default_domain": "bimaterial_rectangle",
        "defaults": {
            "T": 2.0, "dt": 0.01, "mesh_resolution": 60,
            "alpha": 0.003, "ratio": 10.0, "x_int": 1.5,
            "vx": 1.0, "vy": 0.0, "Q": 0.0,
        },
    },
    "advection_diffusion_aquifer": {
        "template": "advection_diffusion_aquifer_template.edp",
        "label": "Advection-Diffusion — Aquifer with Sand Lens Ω₁ in Clay Ω₂",
        "supports_domain": False,
        "default_domain": "aquifer_lens",
        "defaults": {
            "T": 3.0, "dt": 0.02, "mesh_resolution": 60,
            "alpha": 0.003, "ratio": 15.0,
            "vx": 1.0, "vy": 0.0, "Q": 0.0,
        },
    },
    "heat": {
        "template": "heat_diffusion_template.edp",
        "label": "Heat Equation (Diffusion) (C.1.3 i)",
        "supports_domain": True,
        "default_domain": "disk",
        "defaults": {
            "T": 1.0, "dt": 0.05, "mesh_resolution": 50,
            "alpha": 1.0, "Q": 0.0,
        },
    },
    "steady_heat": {
        "template": "steady_heat_template.edp",
        "label": "Steady-State Heat / Poisson (C.1.3 iii)",
        "supports_domain": True,
        "default_domain": "disk",
        "defaults": {
            "T": 0.0, "dt": 0.0, "mesh_resolution": 60,
            "alpha": 1.0, "Q": 1.0,
        },
    },
    "stokes": {
        "template": "stokes_template.edp",
        "label": "Stokes / Creeping flow (C.1.2 iii)",
        "supports_domain": False,          # physics-specific BCs hardcoded
        "defaults": {
            "T": 0.0, "dt": 0.0, "mesh_resolution": 60,
            "alpha": 1.0, "Q": 0.0,        # alpha = μ (viscosity)
        },
    },
    "elasticity": {
        "template": "linear_elasticity_template.edp",
        "label": "Linear Elasticity / Navier-Cauchy (C.1.1 i)",
        "supports_domain": False,          # cantilever geometry hardcoded
        "defaults": {
            "T": 0.0, "dt": 0.0, "mesh_resolution": 30,
            "alpha": 1.0e3,    # Young's modulus E
            "Q": 0.3,          # Poisson's ratio ν
        },
    },
    "eigenvalue": {
        "template": "laplace_eigenvalue_template.edp",
        "label": "Scalar Laplacian eigenvalue (C.1.1 iv)",
        "supports_domain": True,
        "default_domain": "disk",
        "defaults": {
            "T": 0.0, "dt": 0.0, "mesh_resolution": 60,
            "alpha": 0.0, "Q": 0.0,
        },
    },

    # ---- SPRIND figure pack -----------------------------------------------
    "heat_multimaterial": {
        "template": "heat_multimaterial_template.edp",
        "label": "Multi-material steady heat (FreeFEM doc Fig. 3.2)",
        "supports_domain": True,
        "default_domain": "heat_exchanger",
        "defaults": {
            "T": 0.0, "dt": 0.0, "mesh_resolution": 60,
            "alpha": 1.0, "Q": 0.0,
        },
    },
    "airfoil_potential_flow": {
        "template": "airfoil_potential_flow_template.edp",
        "label": "Potential flow around an airfoil (FreeFEM doc §3.5)",
        "supports_domain": True,
        "default_domain": "airfoil_naca0012",
        "defaults": {
            "T": 0.0, "dt": 0.0, "mesh_resolution": 60,
            "alpha": 0.0, "vx": 1.0, "vy": 0.0, "Q": 0.0,
        },
    },
    "airfoil_thermal_trail": {
        "template": "airfoil_thermal_trail_template.edp",
        "label": "Airfoil thermal trail (FreeFEM doc Fig. 3.5)",
        "supports_domain": True,
        "default_domain": "airfoil_naca0012",
        "defaults": {
            "T": 2.5, "dt": 0.05, "mesh_resolution": 70,
            "alpha": 0.1, "vx": 1.0, "vy": 0.0, "Q": 0.0,
        },
    },
    "rotating_hill_cg": {
        "template": "rotating_hill_cg_template.edp",
        "label": "Rotating hill, characteristics-Galerkin (FreeFEM doc §3.6)",
        "supports_domain": True,
        "default_domain": "disk",
        "defaults": {
            "T": 6.283185307,    # one full revolution (2 pi)
            "dt": 0.17,
            "mesh_resolution": 80,
            "alpha": 0.0, "vx": 0.0, "vy": 0.0, "Q": 0.0,
        },
    },
    "rotating_hill_dg": {
        "template": "rotating_hill_dg_template.edp",
        "label": "Rotating hill, P1dc characteristics-Galerkin (FreeFEM doc §3.6)",
        "supports_domain": True,
        "default_domain": "disk",
        "defaults": {
            "T": 6.283185307,
            "dt": 0.17,
            "mesh_resolution": 80,
            "alpha": 0.0, "vx": 0.0, "vy": 0.0, "Q": 0.0,
        },
    },
    "dirichlet_eigenmodes": {
        "template": "dirichlet_eigenmodes_template.edp",
        "label": "First 20 Dirichlet eigenmodes (FreeFEM doc Figs. 9.17-9.18)",
        "supports_domain": True,
        "default_domain": "square",
        "defaults": {
            "T": 0.0, "dt": 0.0, "mesh_resolution": 60,
            "alpha": 0.0, "Q": 0.0,
        },
    },
    "schwarz_overlap": {
        "template": "schwarz_overlap_template.edp",
        "label": "Overlapping Schwarz iteration (FreeFEM doc Fig. 9.25)",
        "supports_domain": True,
        "default_domain": "two_subdomains_overlap",
        "defaults": {
            "T": 0.0, "dt": 0.0, "mesh_resolution": 30,
            "alpha": 1.0, "Q": 1.0,
        },
    },
    "compressible_euler_shock": {
        "template": "compressible_euler_shock_template.edp",
        "label": "Compressible Euler at Mach 2, half-disk (FreeFEM doc Fig. 3.13)",
        "supports_domain": True,
        "default_domain": "half_disk_supersonic",
        "defaults": {
            "T": 1.0, "dt": 0.05, "mesh_resolution": 50,
            "alpha": 0.0, "Q": 0.0,
        },
    },
}


def list_catalogue():
    for slug, entry in CATALOGUE.items():
        flag = "  [geom]" if entry.get("supports_domain") else ""
        print(f"  {slug:26s}  {entry['label']}{flag}")
    print()
    print("Available geometries (for PDEs marked [geom]):")
    for g in GEOMETRIES:
        meta = GEOMETRY_META.get(g, {})
        tag = ""
        if meta.get("multi_mesh"):
            tag += "  [multi-mesh]"
        if meta.get("pde_locked"):
            tag += f"  [paired with {meta['pde_locked']}]"
        print(f"  {g}{tag}")


# function to inject params into the FreeFEM .edp script
def generate_edp_with_params(template_path, output_path, params):
    with open(template_path, 'r') as f:
        template = f.read()

    # Use FreeFEM macros: replace %%T%%, %%dt%% etc.
    for key, value in params.items():
        template = template.replace(f"%%{key}%%", str(value))

    with open(output_path, 'w') as f:
        f.write(template)


def _docker_run(edp_in_workspace):
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{PROJECT_ROOT}:/workspace",
        "-w", "/workspace",
        "antoinehocquet/freefem", "FreeFem++", "-nw", edp_in_workspace,
    ]
    print("Running FreeFEM via Docker:", " ".join(docker_cmd))
    try:
        subprocess.run(docker_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("Simulation failed:", e)


def run_simulation(pde=None, domain=None, overrides=None, use_params_json=True):
    """Run a PDE from the catalogue.

    Precedence (highest wins):
        explicit ``overrides`` dict  >  catalogue defaults  (if ``use_params_json=False``)
        explicit ``overrides`` dict  >  params.json  >  catalogue defaults  (if True)

    The legacy default is ``use_params_json=True``, which preserves the
    historic CLI behaviour. The SPRIND figure driver passes
    ``use_params_json=False`` so that each PDE uses its own catalogue
    defaults (T = 2 pi for the rotating hill, Q = 1 for steady heat, etc.)
    regardless of what the user's ``params.json`` happens to hold.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    params = load_config() if use_params_json else {}
    pde = pde or params.get("pde")
    domain = domain or params.get("domain")

    if pde is None:
        template_edp = os.path.join(EDP_DIR, "heat_disk_template.edp")
        final_edp = os.path.join(EDP_DIR, "heat_disk.edp")
        print("Generating heat_disk.edp from legacy template...")
        generate_edp_with_params(template_edp, final_edp, params)
        _docker_run("/workspace/edp/heat_disk.edp")
        return

    if pde not in CATALOGUE:
        raise ValueError(
            f"Unknown PDE '{pde}'. Available: {sorted(CATALOGUE.keys())}"
        )

    entry = CATALOGUE[pde]
    merged = dict(entry["defaults"])
    merged.update({k: v for k, v in params.items() if k not in ("pde", "domain")})
    if overrides:
        merged.update(overrides)

    # Resolve geometry
    if entry.get("supports_domain"):
        domain = domain or entry["default_domain"]
        if domain not in GEOMETRIES:
            raise ValueError(
                f"Unknown domain '{domain}'. Available: {list(GEOMETRIES)}"
            )
        # PDE-locked geometries: warn if the user pairs them with a different PDE.
        meta = GEOMETRY_META.get(domain, {})
        locked = meta.get("pde_locked")
        if locked is not None and locked != pde:
            print(
                f"   note: geometry '{domain}' is meaningful only with PDE "
                f"'{locked}'; using it with '{pde}' may not give physical "
                f"results."
            )
        merged["domain"] = domain
    elif domain:
        print(
            f"   note: PDE '{pde}' has a physics-specific geometry; "
            f"--domain {domain} ignored."
        )

    template_edp = os.path.join(CATALOGUE_DIR, entry["template"])
    final_edp = os.path.join(CATALOGUE_DIR, f"{pde}.edp")

    print(f"== {entry['label']} ==")
    if entry.get("supports_domain"):
        print(f"   geometry:   {merged['domain']}")
    print(f"   parameters: {merged}")
    generate_edp_with_params(template_edp, final_edp, merged)
    _docker_run(f"/workspace/edp/catalogue/{pde}.edp")


def run_llg_simulation():
    """Run the Landau-Lifshitz-Gilbert example via the Docker FreeFEM image."""
    os.makedirs(os.path.join(DATA_DIR, "data_llg"), exist_ok=True)
    _docker_run("/workspace/edp/initsllg.edp")
