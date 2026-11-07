import numpy as np
import pandas as pd

from src.strategy import Generate_Trajectory_BS, Pricing_Anthemis

SEED = 42


def _bs_paths(seed, n_paths=100, n_dates=5):
    riskfree = [0.01] * n_dates
    delta = [1.0] * n_dates
    vol = 0.20
    rng = np.random.default_rng(seed)
    matrice_alea = rng.normal(0, 1, size=(n_paths, n_dates - 1, 1)) * vol
    return Generate_Trajectory_BS([100.0], riskfree, 0.02, vol, delta, matrice_alea, nbre_path=n_paths)


def test_bs_diffusion_shape():
    n_paths, n_dates = 100, 5
    diff = _bs_paths(SEED, n_paths, n_dates)
    assert len(diff) == n_dates
    assert diff[0].shape == (n_paths, 1)
    assert np.allclose(diff[0].values, 100.0)


def test_bs_diffusion_is_reproducible():
    a = _bs_paths(SEED)
    b = _bs_paths(SEED)
    for t in a:
        assert np.array_equal(a[t].values, b[t].values)


def _price(final_level, coupon_du=0):
    diff = {0: pd.DataFrame([100.0] * 50), 1: pd.DataFrame([final_level] * 50)}
    return Pricing_Anthemis(
        diffusion_matrix=diff,
        coupon_du=coupon_du,
        strike=100.0,
        flt_barrier_bonus=0.70,
        DF={1: 0.95},
        flt_bonus=5.5,
        capital_barrier=0.60,
        redemption_level=100.0,
    )


def test_pricing_above_both_barriers():
    # one bonus earned at maturity, capital repaid at 100
    assert np.isclose(_price(105.0), 0.95 * (5.5 + 100.0))


def test_pricing_between_barriers():
    # below the 70% bonus barrier, above the 60% capital barrier: capital only
    assert np.isclose(_price(65.0), 0.95 * 100.0)


def test_pricing_below_capital_barrier():
    # below 60%: no bonus, capital loss indexed on the index
    assert np.isclose(_price(50.0), 0.95 * 100.0 * 50.0 / 100.0)


def test_pricing_counts_locked_coupons():
    assert np.isclose(_price(50.0, coupon_du=3), 0.95 * (3 * 5.5 + 50.0))
