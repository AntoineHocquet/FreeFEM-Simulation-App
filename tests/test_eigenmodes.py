"""Numerical-truth check for the Dirichlet eigenvalues on the unit square.

Closed-form spectrum on (0, pi)^2 with homogeneous Dirichlet BCs:
    lambda_{n,m} = n^2 + m^2,
    phi_{n,m}(x, y) = sin(n x) sin(m y).

The current `square.idp` is the unit square (0, 1)^2 (a smaller test domain
than (0, pi)^2).  By a similarity argument, the eigenvalues on (0, L)^2 are
``(pi / L)^2 (n^2 + m^2)``.  We test against that exact formula.

The test reads ``data/eigenvalues.csv`` produced by the
``dirichlet_eigenmodes`` PDE template.  When that file is absent (no FreeFEM
run yet), the test is skipped rather than failing.
"""

from __future__ import annotations

import math
import os

import pytest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV_CSV = os.path.join(ROOT, "data", "eigenvalues.csv")
CACHED_EV_CSV = os.path.join(
    ROOT, "data", "sprind_figures", "_csv", "dirichlet_eigenmodes_eigenvalues.csv"
)


def _expected_eigenvalues_unit_square():
    """First few (n, m) modes on (0, 1)^2, sorted by eigenvalue."""
    pairs = []
    for n in range(1, 6):
        for m in range(1, 6):
            pairs.append((n, m, (math.pi ** 2) * (n * n + m * m)))
    pairs.sort(key=lambda nmL: nmL[2])
    return pairs


def _load_eigenvalues():
    for path in (EV_CSV, CACHED_EV_CSV):
        if os.path.exists(path) and os.path.getsize(path) > 0:
            import pandas as pd
            return pd.read_csv(path)
    return None


@pytest.mark.parametrize("idx,nm", [
    (0, (1, 1)),
    (1, (1, 2)),  # degenerate with (2, 1)
    (2, (2, 1)),
    (3, (2, 2)),
    (4, (1, 3)),  # degenerate with (3, 1)
    (5, (3, 1)),
])
def test_unit_square_eigenvalues(idx, nm):
    df = _load_eigenvalues()
    if df is None:
        pytest.skip("eigenvalues.csv not present — run dirichlet_eigenmodes first.")
    expected = _expected_eigenvalues_unit_square()
    n, m = nm
    expected_lambda = (math.pi ** 2) * (n * n + m * m)
    if idx >= len(df):
        pytest.skip(f"only {len(df)} eigenvalues available, need {idx + 1}")
    got = float(df.iloc[idx]["lambda"])
    rel_err = abs(got - expected_lambda) / expected_lambda
    assert rel_err < 0.01, (
        f"mode {idx + 1} (n={n}, m={m}): expected lambda = {expected_lambda:.4f}, "
        f"got {got:.4f} (rel err {rel_err:.2%})"
    )
