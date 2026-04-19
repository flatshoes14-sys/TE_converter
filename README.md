# Thermoelectric Converter App

Personal Streamlit app for thermoelectric property **unit conversion** and **PF / zT calculations**.

## Features
- Unit conversion for:
  - Seebeck coefficient
  - Electrical conductivity
  - Electrical resistivity
  - Thermal conductivity
  - Temperature
- Power factor calculator: `PF = S^2 * sigma`
- zT calculator: `zT = S^2 * sigma * T / kappa`
- Automatic conductivity ↔ resistivity reciprocal outputs
- Batch CSV processing for conversion, PF, and zT
- Pint-based unit handling with all internal calculations in SI units

## Project structure
- `app.py` – Streamlit UI and CSV batch workflow
- `converter.py` – property conversion helpers and conductivity/resistivity reciprocity
- `formulas.py` – SI thermoelectric formulas (PF and zT)
- `units.py` – Pint registry, supported units, SI conversion utilities
- `validators.py` – physical input validation helpers
- `sample_data.csv` – sample input for batch mode
- `tests/test_conversion.py` – unit conversion tests
- `tests/test_formulas.py` – formula tests

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
streamlit run app.py
```

## Run tests
```bash
pytest
```

## Notes
- Temperatures are accepted as `K` or `degC`, but converted internally to `K`.
- Thermal conductivity must be positive for zT calculations.
- Batch mode handles missing values gracefully and reports row warnings.
- PF uses `S^2`, so Seebeck sign does not change PF magnitude.
