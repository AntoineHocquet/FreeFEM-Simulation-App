# main.py
import argparse
import runpy
import os
from simulate import run_simulation, run_llg_simulation
from visualize import generate_visualizations
from visualize_gif import generate_gif


def main():
    parser = argparse.ArgumentParser(description="FreeFEM Simulation Pipeline")
    parser.add_argument(
        "--run",
        choices=["sim", "viz", "gif", "llg", "llg-gif", "all"],
        default="all",
        help="Choose what to run: heat-equation sim/viz/gif, LLG sim, LLG gif, or all"
    )
    args = parser.parse_args()

    if args.run in ["sim", "all"]:
        print("Running simulation...")
        run_simulation()

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
