# main.py
import argparse
import runpy
import os
from simulate import run_simulation, run_llg_simulation, list_catalogue, CATALOGUE
from visualize import generate_visualizations
from visualize_gif import generate_gif


def main():
    parser = argparse.ArgumentParser(description="FreeFEM Simulation Pipeline")
    parser.add_argument(
        "--run",
        choices=["sim", "viz", "gif", "llg", "llg-gif", "all", "list"],
        default="all",
        help=(
            "Choose what to run: sim/viz/gif (heat-equation pipeline), llg, "
            "llg-gif, all, or 'list' to print the PDE catalogue."
        ),
    )
    parser.add_argument(
        "--pde",
        default=None,
        choices=sorted(CATALOGUE.keys()),
        help=(
            "Pick a PDE from the catalogue (advection_diffusion, heat, "
            "steady_heat, stokes, elasticity, eigenvalue). Overrides "
            "params.json['pde']. Use --run list to see the full list."
        ),
    )
    args = parser.parse_args()

    if args.run == "list":
        print("Available PDEs in the catalogue:")
        list_catalogue()
        return

    if args.run in ["sim", "all"]:
        print("Running simulation...")
        run_simulation(pde=args.pde)

    if args.run in ["viz", "all"]:
        print("Generating visualization...")
        generate_visualizations()

    if args.run in ["gif", "all"]:
        generate_gif()

    if args.run == "llg":
        run_llg_simulation()

    if args.run == "llg-gif":
        here = os.path.dirname(os.path.abspath(__file__))
        runpy.run_path(os.path.join(here, "visualize_llg_gif.py"), run_name="__main__")


if __name__ == "__main__":
    main()
