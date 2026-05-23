# main.py
import argparse
import runpy
import os
from simulate import (
    run_simulation, run_llg_simulation, list_catalogue, CATALOGUE, GEOMETRIES,
)
from visualize import generate_visualizations
from visualize_gif import generate_gif
from visualize_surface import generate_surface
from visualize_heatmap import generate_heatmap


def main():
    parser = argparse.ArgumentParser(description="FreeFEM Simulation Pipeline")
    parser.add_argument(
        "--run",
        choices=["sim", "viz", "gif", "surface", "heatmap", "llg", "llg-gif", "all", "list"],
        default="all",
        help=(
            "Choose what to run: sim/viz/gif/surface/heatmap (pipeline stages), "
            "llg, llg-gif, all, or 'list' to print the PDE catalogue. "
            "'surface' renders the CSV as a 3D nappe de valeurs (matplotlib). "
            "'heatmap' renders the CSV as a 2D seaborn heatmap."
        ),
    )
    parser.add_argument(
        "--pde",
        default=None,
        choices=sorted(CATALOGUE.keys()),
        help=(
            "Pick a PDE from the catalogue. Overrides params.json['pde']. "
            "Use --run list to see the full catalogue."
        ),
    )
    parser.add_argument(
        "--domain",
        default=None,
        choices=list(GEOMETRIES),
        help=(
            "Geometry on which to solve the PDE. Ignored for PDEs with "
            "physics-specific geometries (stokes, elasticity). Overrides "
            "params.json['domain']."
        ),
    )
    parser.add_argument(
        "--figures",
        choices=["sprind"],
        default=None,
        help=(
            "Generate a named figure pack from `data/<pack>_figures/`. "
            "Currently the only pack is 'sprind' (runs the seven simulations "
            "anchored to FreeFEM doc figures and emits PNGs)."
        ),
    )
    args = parser.parse_args()

    if args.figures == "sprind":
        # Lazy import so the rest of the CLI does not depend on the figure stack.
        from sprind_figures import generate_sprind_figure_pack
        generate_sprind_figure_pack()
        return

    if args.run == "list":
        print("Available PDEs in the catalogue:")
        list_catalogue()
        return

    if args.run in ["sim", "all"]:
        print("Running simulation...")
        run_simulation(pde=args.pde, domain=args.domain)

    if args.run in ["viz", "all"]:
        print("Generating visualization...")
        generate_visualizations()

    if args.run in ["gif", "all"]:
        generate_gif()

    if args.run == "surface":
        generate_surface()

    if args.run == "heatmap":
        generate_heatmap()

    if args.run == "llg":
        run_llg_simulation()

    if args.run == "llg-gif":
        here = os.path.dirname(os.path.abspath(__file__))
        runpy.run_path(os.path.join(here, "visualize_llg_gif.py"), run_name="__main__")


if __name__ == "__main__":
    main()
