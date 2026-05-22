# src/simulate.py
import subprocess
import os
import platform
from config import load_config

# function to inject params into the FreeFEM .edp script
def generate_edp_with_params(template_path, output_path, params):
    with open(template_path, 'r') as f:
        template = f.read()

    # Use FreeFEM macros: replace %%T%%, %%dt%% etc.
    for key, value in params.items():
        template = template.replace(f"%%{key}%%", str(value))

    with open(output_path, 'w') as f:
        f.write(template)

# function to run FreeFEM via Docker
def run_simulation():
    current_os = platform.system()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    edp_path = os.path.join(project_root, "edp")
    data_path = os.path.join(project_root, "data")
    os.makedirs(data_path, exist_ok=True)

    # Load parameters from JSON
    params = load_config()

    # Template and final EDP paths
    template_edp = os.path.join(edp_path, "heat_disk_template.edp")
    final_edp = os.path.join(edp_path, "heat_disk.edp")

    print("Generating .edp file with parameters from params.json...")
    generate_edp_with_params(template_edp, final_edp, params)

    # Mount the project root at /workspace inside the container.
    # The .edp scripts read from /workspace/edp and write to /workspace/data,
    # so outputs land in the host project's data/ directory.
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{project_root}:/workspace",
        "-w", "/workspace",
        "antoinehocquet/freefem", "FreeFem++", "-nw", "/workspace/edp/heat_disk.edp"
    ]

    print("Running FreeFEM via Docker...")
    try:
        subprocess.run(docker_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("Simulation failed:", e)


def run_llg_simulation():
    """Run the Landau-Lifshitz-Gilbert example via the Docker FreeFEM image."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, "data", "data_llg")
    os.makedirs(data_path, exist_ok=True)

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{project_root}:/workspace",
        "-w", "/workspace",
        "antoinehocquet/freefem", "FreeFem++", "-nw", "/workspace/edp/initsllg.edp"
    ]

    print("Running LLG simulation via Docker...")
    try:
        subprocess.run(docker_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("LLG simulation failed:", e)