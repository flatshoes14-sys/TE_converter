"""Higher-level conversion helpers for thermoelectric workflows."""

from __future__ import annotations

from typing import Dict

from units import convert_all_units, from_si, to_si


PROPERTY_LABEL_TO_KEY = {
    "Seebeck coefficient": "seebeck",
    "Electrical conductivity": "conductivity",
    "Electrical resistivity": "resistivity",
    "Thermal conductivity": "thermal_conductivity",
    "Temperature": "temperature",
}


def convert_property(value: float, from_unit: str, property_key: str) -> Dict[str, float]:
    """Convert a property value from one unit to all supported units."""
    return convert_all_units(value=value, from_unit=from_unit, property_name=property_key)


def conductivity_to_resistivity(conductivity_value: float, conductivity_unit: str, to_unit: str = "ohm*m") -> float:
    """Convert conductivity input to resistivity output via SI."""
    sigma_si = to_si(conductivity_value, conductivity_unit, "conductivity")
    if sigma_si == 0:
        raise ValueError("Conductivity must be non-zero for reciprocal conversion.")
    rho_si = 1.0 / sigma_si
    return from_si(rho_si, to_unit, "resistivity")


def resistivity_to_conductivity(resistivity_value: float, resistivity_unit: str, to_unit: str = "S/m") -> float:
    """Convert resistivity input to conductivity output via SI."""
    rho_si = to_si(resistivity_value, resistivity_unit, "resistivity")
    if rho_si == 0:
        raise ValueError("Resistivity must be non-zero for reciprocal conversion.")
    sigma_si = 1.0 / rho_si
    return from_si(sigma_si, to_unit, "conductivity")
