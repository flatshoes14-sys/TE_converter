"""Core thermoelectric formulas in SI units."""

from __future__ import annotations


def power_factor_w_mk2(seebeck_vpk: float, conductivity_spm: float) -> float:
    """Compute power factor in W/m/K^2 using SI inputs.

    Formula: PF = S^2 * sigma
    """
    return (seebeck_vpk**2) * conductivity_spm


def zt_dimensionless(
    seebeck_vpk: float,
    conductivity_spm: float,
    temperature_k: float,
    thermal_conductivity_wmk: float,
) -> float:
    """Compute dimensionless zT in SI units.

    Formula: zT = S^2 * sigma * T / kappa
    """
    return power_factor_w_mk2(seebeck_vpk, conductivity_spm) * temperature_k / thermal_conductivity_wmk
