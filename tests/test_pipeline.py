"""End-to-end smoke tests.

Two flavours:

* ``test_default_pipeline_outputs`` — checks the legacy artifacts produced by
  ``simulate --run all`` (heat-equation CSV + GIF) still appear.
* ``test_pde_geometry_pairs`` — parametrized over every (PDE, geometry) pair
  registered for the SPRIND figure pack. Each test verifies that the
  generated CSV exists and that the row count looks plausible for the
  expected number of time steps.

The simulations themselves are not run by the test suite — they require
Docker + FreeFEM. The tests check that the *registration* is consistent
(template file exists, geometry .idp exists, defaults are well formed) and
that CSVs produced by a prior ``simulate --figures sprind`` run pass basic
sanity checks. Use the ``--with-docker`` env flag to also invoke FreeFEM.
"""

from __future__ import annotations

import math
import os
import sys

import pytest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from simulate import CATALOGUE, GEOMETRIES, CATALOGUE_DIR  # noqa: E402

GEOMETRIES_DIR = os.path.join(ROOT, "edp", "geometries")
DATA_DIR = os.path.join(ROOT, "data")


# ---------------------------------------------------------------------------
#  Catalogue self-consistency (always runs)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("pde_slug", sorted(CATALOGUE.keys()))
def test_pde_template_file_exists(pde_slug):
    entry = CATALOGUE[pde_slug]
    path = os.path.join(CATALOGUE_DIR, entry["template"])
    assert os.path.isfile(path), f"template missing for {pde_slug}: {path}"


@pytest.mark.parametrize("geom", GEOMETRIES)
def test_geometry_file_exists(geom):
    path = os.path.join(GEOMETRIES_DIR, f"{geom}.idp")
    assert os.path.isfile(path), f"geometry .idp missing: {path}"


@pytest.mark.parametrize("pde_slug", sorted(CATALOGUE.keys()))
def test_pde_defaults_well_formed(pde_slug):
    entry = CATALOGUE[pde_slug]
    assert "label" in entry
    assert isinstance(entry.get("defaults", {}), dict)
    assert "mesh_resolution" in entry["defaults"]
    if entry.get("supports_domain"):
        default_domain = entry.get("default_domain")
        assert default_domain in GEOMETRIES, \
            f"{pde_slug} default_domain {default_domain!r} not registered"


# ---------------------------------------------------------------------------
#  Legacy default-pipeline smoke (only runs if the user has produced the
#  legacy artifacts in data/).
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    not os.path.exists(os.path.join(DATA_DIR, "solution_data.csv")),
    reason="solution_data.csv not present — run `simulate --run all` first.",
)
def test_default_csv_nonempty():
    p = os.path.join(DATA_DIR, "solution_data.csv")
    assert os.path.getsize(p) > 0, "CSV file is empty!"


@pytest.mark.skipif(
    not os.path.exists(os.path.join(DATA_DIR, "heat_equation_simulation.gif")),
    reason="heat_equation_simulation.gif not present — run `simulate --run gif`.",
)
def test_default_gif_nonempty():
    p = os.path.join(DATA_DIR, "heat_equation_simulation.gif")
    assert os.path.getsize(p) > 0, "GIF file is empty!"


# ---------------------------------------------------------------------------
#  Per-PDE smoke for the SPRIND figure-pack artefacts (only runs if the
#  driver has previously generated the cached CSVs in
#  data/sprind_figures/_csv/).
# ---------------------------------------------------------------------------
_SPRIND_CSV_DIR = os.path.join(DATA_DIR, "sprind_figures", "_csv")

# (cached-csv name,  expected_min_rows,  expected_time_steps_or_None)
_SPRIND_EXPECTATIONS = {
    "heat_exchanger_solution.csv":          (10, 1),
    "airfoil_psi.csv":                       (10, None),
    "airfoil_trail.csv":                     (10, None),
    "rotating_hill_cg.csv":                  (10, None),
    "rotating_hill_dg.csv":                  (10, None),
    "dirichlet_eigenmodes_solution.csv":     (10, 20),
    "schwarz_overlap_solution.csv":          (10, 1),
    "schwarz_convergence.csv":               (2,  None),
    "lshape_solution.csv":                   (10, 1),
    "euler_final_fields.csv":                (10, None),
}


@pytest.mark.parametrize("csv_name,expectation", _SPRIND_EXPECTATIONS.items())
def test_sprind_csv_artifacts(csv_name, expectation):
    path = os.path.join(_SPRIND_CSV_DIR, csv_name)
    if not os.path.exists(path):
        pytest.skip(f"{csv_name} not yet produced — run `simulate --figures sprind`.")
    min_rows, expected_steps = expectation
    import pandas as pd
    df = pd.read_csv(path)
    assert len(df) >= min_rows, f"too few rows in {csv_name}: {len(df)}"
    if expected_steps is not None and "time" in df.columns:
        unique = df["time"].nunique()
        assert unique == expected_steps, \
            f"{csv_name}: expected {expected_steps} time/mode slices, got {unique}"
