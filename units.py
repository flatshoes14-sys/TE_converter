"""Unit registry and conversion helpers for thermoelectric properties."""

from __future__ import annotations

from typing import Dict

from pint import UnitRegistry
from pint.errors import PintError

ureg = UnitRegistry(autoconvert_offset_to_baseunit=True)
Q_ = ureg.Quantity

# Custom shorthand aliases commonly used in TE literature.
ureg.define("uV = microvolt")
ureg.define("mohm = milliohm")

PROPERTY_UNITS: Dict[str, list[str]] = {
    "seebeck": ["V/K", "mV/K", "uV/K"],
    "conductivity": ["S/m", "S/cm"],
    "resistivity": ["ohm*m", "ohm*cm", "mohm*cm"],
    "thermal_conductivity": ["W/m/K", "mW/cm/K"],
    "temperature": ["K", "degC"],
    "power_factor": ["W/m/K^2", "mW/m/K^2", "uW/cm/K^2"],
}

SI_UNITS: Dict[str, str] = {
    "seebeck": "V/K",
    "conductivity": "S/m",
    "resistivity": "ohm*m",
    "thermal_conductivity": "W/m/K",
    "temperature": "K",
    "power_factor": "W/m/K^2",
}


def to_si(value: float, from_unit: str, property_name: str) -> float:
    """Convert a property value into the required SI unit used internally."""
    try:
        qty = Q_(value, from_unit)
        return qty.to(SI_UNITS[property_name]).magnitude
    except (PintError, KeyError) as exc:
        raise ValueError(f"Failed to convert {property_name} from {from_unit}: {exc}") from exc


def from_si(value_si: float, to_unit: str, property_name: str) -> float:
    """Convert SI value into a selected display unit."""
    try:
        qty = Q_(value_si, SI_UNITS[property_name])
        return qty.to(to_unit).magnitude
    except (PintError, KeyError) as exc:
        raise ValueError(f"Failed to convert {property_name} to {to_unit}: {exc}") from exc


def convert_all_units(value: float, from_unit: str, property_name: str) -> Dict[str, float]:
    """Convert input value to all supported units for the property."""
    value_si = to_si(value=value, from_unit=from_unit, property_name=property_name)
    return {unit: from_si(value_si=value_si, to_unit=unit, property_name=property_name) for unit in PROPERTY_UNITS[property_name]}
