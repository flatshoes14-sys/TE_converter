from converter import conductivity_to_resistivity, resistivity_to_conductivity
from units import convert_all_units, to_si


def test_seebeck_uv_to_v_per_k() -> None:
    val_si = to_si(200.0, "uV/K", "seebeck")
    assert val_si == 200e-6


def test_conductivity_s_cm_to_s_m() -> None:
    val_si = to_si(1000.0, "S/cm", "conductivity")
    assert val_si == 100000.0


def test_convert_resistivity_units() -> None:
    converted = convert_all_units(1.0, "mohm*cm", "resistivity")
    assert abs(converted["ohm*m"] - 1e-5) < 1e-12
    assert abs(converted["ohm*cm"] - 1e-3) < 1e-12


def test_sigma_rho_reciprocal() -> None:
    rho = conductivity_to_resistivity(1000.0, "S/cm", to_unit="mohm*cm")
    sigma = resistivity_to_conductivity(rho, "mohm*cm", to_unit="S/cm")
    assert abs(sigma - 1000.0) < 1e-9
