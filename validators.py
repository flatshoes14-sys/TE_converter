"""Validation utilities for thermoelectric inputs."""

from __future__ import annotations

from typing import Optional


def validate_temperature_k(temperature_k: float) -> Optional[str]:
    """Validate absolute temperature in Kelvin."""
    if temperature_k < 0:
        return "Absolute temperature cannot be below 0 K."
    return None


def validate_thermal_conductivity(kappa_wmk: float) -> Optional[str]:
    """Validate thermal conductivity for zT calculation."""
    if kappa_wmk <= 0:
        return "Thermal conductivity must be greater than zero."
    return None


def validate_numeric(value: float, field_name: str) -> Optional[str]:
    """Guard against NaN/inf style invalid numerical values."""
    if value is None:
        return f"{field_name} is missing."
    try:
        _ = float(value)
    except (TypeError, ValueError):
        return f"{field_name} must be numeric."
    return None
