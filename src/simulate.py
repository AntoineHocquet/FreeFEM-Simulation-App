# src/simulate.py
import subprocess
import os
import platform
from config import load_config


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDP_DIR = os.path.join(PROJECT_ROOT, "edp")
CATALOGUE_DIR = os.path.join(EDP_DIR, "catalogue")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


# ---------------------------------------------------------------------------
#  Catalogue of industrial PDEs (notation follows the report appendix C.1.x)
# ---------------------------------------------------------------------------
#  Each entry maps a short slug → (template file, default parameters, label).
#  Parameter names match the symbols of the captured report:
#      α  — diffusivity (or, in elasticity, Young's modulus E)
#      v  — velocity (vx, vy components)
#      Q  — volumetric source (or Poisson's ratio for elasticity)
#      T  — final time     T_end       (the time horizon, not the unknown)
#      dt — time step      Δt
#      mesh_resolution — N points along the boundary
# ---------------------------------------------------------------------------
# Geometries available as the "domain" axis (edp/geometries/<name>.idp).
# Each is includable by any PDE template that opts in via supports_domain=True.
GEOMETRIES = ("disk", "square", "rectangle", "lshape", "annulus")

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
}


def list_catalogue():
    for slug, entry in CATALOGUE.items():
        flag = "  [geom]" if entry.get("supports_domain") else ""
        print(f"  {slug:22s}  {entry['label']}{flag}")
    print()
    print("Available geometries (for PDEs marked [geom]):")
    for g in GEOMETRIES:
        print(f"  {g}")


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


def run_simulation(pde=None, domain=None):
    """Run a PDE from the catalogue. ``pde`` / ``domain`` override params.json.

    Falls back to the legacy ``edp/heat_disk_template.edp`` when called with
    no ``pde`` argument and no ``pde`` key in params.json, so old workflows
    keep working unchanged.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    params = load_config()
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

    # Resolve geometry
    if entry.get("supports_domain"):
        domain = domain or entry["default_domain"]
        if domain not in GEOMETRIES:
            raise ValueError(
                f"Unknown domain '{domain}'. Available: {list(GEOMETRIES)}"
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
