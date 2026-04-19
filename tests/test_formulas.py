from formulas import power_factor_w_mk2, zt_dimensionless


def test_power_factor_formula() -> None:
    # S = 200 uV/K -> 2e-4 V/K, sigma = 1e5 S/m
    pf = power_factor_w_mk2(2e-4, 1e5)
    assert abs(pf - 0.004) < 1e-12


def test_zt_formula() -> None:
    zt = zt_dimensionless(2e-4, 1e5, 300, 1.5)
    assert abs(zt - 0.8) < 1e-12
