"""Streamlit app for thermoelectric unit conversion and calculations."""

from __future__ import annotations

import io
from typing import Dict, List

import pandas as pd
import streamlit as st

from converter import (
    PROPERTY_LABEL_TO_KEY,
    conductivity_to_resistivity,
    convert_property,
    resistivity_to_conductivity,
)
from formulas import power_factor_w_mk2, zt_dimensionless
from units import PROPERTY_UNITS, from_si, to_si
from validators import validate_temperature_k, validate_thermal_conductivity

st.set_page_config(page_title="TE Converter", layout="wide")
st.title("Thermoelectric Property Converter & Calculator")
st.caption("All internal calculations are performed in SI units via Pint.")


def _show_conversion_results(results: Dict[str, float], title: str = "Converted values") -> None:
    st.subheader(title)
    table_df = pd.DataFrame(
        [{"Unit": unit, "Value": value} for unit, value in results.items()]
    )
    st.dataframe(table_df, hide_index=True, use_container_width=True)


def _show_pf_outputs(pf_si: float) -> None:
    pf_outputs = {
        unit: from_si(pf_si, unit, "power_factor") for unit in PROPERTY_UNITS["power_factor"]
    }
    _show_conversion_results(pf_outputs, title="Power factor outputs")


def _build_batch_result(df: pd.DataFrame, errors: List[str]) -> pd.DataFrame:
    if errors:
        st.warning(f"Processed with {len(errors)} row-level warning(s).")
        with st.expander("Row warnings"):
            for err in errors:
                st.write(f"- {err}")
    return df


def _process_batch_convert(
    df: pd.DataFrame,
    source_col: str,
    source_unit: str,
    property_key: str,
) -> pd.DataFrame:
    results = df.copy()
    series = pd.to_numeric(results[source_col], errors="coerce")
    for unit in PROPERTY_UNITS[property_key]:
        results[f"{source_col}__{unit}"] = series.apply(
            lambda val: from_si(to_si(val, source_unit, property_key), unit, property_key)
            if pd.notna(val)
            else pd.NA
        )
    return results


def _process_batch_pf(
    df: pd.DataFrame,
    seebeck_col: str,
    seebeck_unit: str,
    sigma_col: str,
    sigma_unit: str,
) -> pd.DataFrame:
    results = df.copy()
    errors: List[str] = []

    def row_pf(row: pd.Series, idx: int) -> float:
        s_val = pd.to_numeric(row[seebeck_col], errors="coerce")
        sigma_val = pd.to_numeric(row[sigma_col], errors="coerce")
        if pd.isna(s_val) or pd.isna(sigma_val):
            errors.append(f"Row {idx}: missing/invalid Seebeck or conductivity value.")
            return pd.NA
        s_si = to_si(float(s_val), seebeck_unit, "seebeck")
        sigma_si = to_si(float(sigma_val), sigma_unit, "conductivity")
        return power_factor_w_mk2(s_si, sigma_si)

    results["PF__W/m/K^2"] = [row_pf(row, i) for i, row in results.iterrows()]
    for unit in PROPERTY_UNITS["power_factor"]:
        results[f"PF__{unit}"] = results["PF__W/m/K^2"].apply(
            lambda val: from_si(val, unit, "power_factor") if pd.notna(val) else pd.NA
        )
    return _build_batch_result(results, errors)


def _process_batch_zt(
    df: pd.DataFrame,
    seebeck_col: str,
    seebeck_unit: str,
    sigma_col: str,
    sigma_unit: str,
    temp_col: str,
    temp_unit: str,
    kappa_col: str,
    kappa_unit: str,
) -> pd.DataFrame:
    results = df.copy()
    errors: List[str] = []

    def row_zt(row: pd.Series, idx: int) -> float:
        s_val = pd.to_numeric(row[seebeck_col], errors="coerce")
        sigma_val = pd.to_numeric(row[sigma_col], errors="coerce")
        t_val = pd.to_numeric(row[temp_col], errors="coerce")
        k_val = pd.to_numeric(row[kappa_col], errors="coerce")
        if any(pd.isna(v) for v in [s_val, sigma_val, t_val, k_val]):
            errors.append(f"Row {idx}: one or more required values are missing/invalid.")
            return pd.NA

        s_si = to_si(float(s_val), seebeck_unit, "seebeck")
        sigma_si = to_si(float(sigma_val), sigma_unit, "conductivity")
        t_si = to_si(float(t_val), temp_unit, "temperature")
        k_si = to_si(float(k_val), kappa_unit, "thermal_conductivity")

        temp_error = validate_temperature_k(t_si)
        if temp_error:
            errors.append(f"Row {idx}: {temp_error}")
            return pd.NA

        kappa_error = validate_thermal_conductivity(k_si)
        if kappa_error:
            errors.append(f"Row {idx}: {kappa_error}")
            return pd.NA

        return zt_dimensionless(s_si, sigma_si, t_si, k_si)

    results["zT"] = [row_zt(row, i) for i, row in results.iterrows()]
    return _build_batch_result(results, errors)


tab_converter, tab_pf, tab_zt, tab_batch = st.tabs(
    ["Unit Converter", "Power Factor Calculator", "zT Calculator", "Batch CSV Processor"]
)

with tab_converter:
    st.header("Unit Converter")
    property_label = st.selectbox("Property", list(PROPERTY_LABEL_TO_KEY.keys()))
    property_key = PROPERTY_LABEL_TO_KEY[property_label]
    in_unit = st.selectbox("Input unit", PROPERTY_UNITS[property_key])
    value = st.number_input("Input value", value=0.0, format="%.8g")

    if st.button("Convert", key="convert_button"):
        converted = convert_property(value, in_unit, property_key)
        _show_conversion_results(converted)

        if property_key == "conductivity":
            try:
                rho_outputs = {
                    unit: conductivity_to_resistivity(value, in_unit, to_unit=unit)
                    for unit in PROPERTY_UNITS["resistivity"]
                }
                _show_conversion_results(rho_outputs, "Derived electrical resistivity")
            except ValueError as exc:
                st.warning(str(exc))

        if property_key == "resistivity":
            try:
                sigma_outputs = {
                    unit: resistivity_to_conductivity(value, in_unit, to_unit=unit)
                    for unit in PROPERTY_UNITS["conductivity"]
                }
                _show_conversion_results(sigma_outputs, "Derived electrical conductivity")
            except ValueError as exc:
                st.warning(str(exc))

with tab_pf:
    st.header("Power Factor Calculator")
    st.info("PF = S²·σ. The sign of Seebeck does not affect PF magnitude.")

    s_pf_col, sigma_pf_col = st.columns(2)
    with s_pf_col:
        s_pf_val = st.number_input("Seebeck", value=200.0, format="%.8g", key="pf_s")
        s_pf_unit = st.selectbox("Seebeck unit", PROPERTY_UNITS["seebeck"], key="pf_s_u")
    with sigma_pf_col:
        sigma_pf_val = st.number_input("Conductivity", value=1e5, format="%.8g", key="pf_sig")
        sigma_pf_unit = st.selectbox(
            "Conductivity unit", PROPERTY_UNITS["conductivity"], key="pf_sig_u"
        )

    if st.button("Calculate PF", key="calc_pf"):
        s_si = to_si(s_pf_val, s_pf_unit, "seebeck")
        sigma_si = to_si(sigma_pf_val, sigma_pf_unit, "conductivity")
        pf_si = power_factor_w_mk2(s_si, sigma_si)
        _show_pf_outputs(pf_si)

        try:
            rho_vals = {
                unit: conductivity_to_resistivity(sigma_pf_val, sigma_pf_unit, to_unit=unit)
                for unit in PROPERTY_UNITS["resistivity"]
            }
            _show_conversion_results(rho_vals, "Derived resistivity from conductivity input")
        except ValueError as exc:
            st.warning(str(exc))

with tab_zt:
    st.header("zT Calculator")
    st.info("zT = S²·σ·T / κ")

    col1, col2 = st.columns(2)
    with col1:
        s_zt_val = st.number_input("Seebeck", value=200.0, format="%.8g", key="zt_s")
        s_zt_unit = st.selectbox("Seebeck unit", PROPERTY_UNITS["seebeck"], key="zt_s_u")

        t_zt_val = st.number_input("Temperature", value=300.0, format="%.8g", key="zt_t")
        t_zt_unit = st.selectbox("Temperature unit", PROPERTY_UNITS["temperature"], key="zt_t_u")
    with col2:
        sigma_zt_val = st.number_input("Conductivity", value=1e5, format="%.8g", key="zt_sig")
        sigma_zt_unit = st.selectbox(
            "Conductivity unit", PROPERTY_UNITS["conductivity"], key="zt_sig_u"
        )

        kappa_zt_val = st.number_input(
            "Thermal conductivity", value=1.5, format="%.8g", key="zt_k"
        )
        kappa_zt_unit = st.selectbox(
            "Thermal conductivity unit",
            PROPERTY_UNITS["thermal_conductivity"],
            key="zt_k_u",
        )

    if st.button("Calculate zT", key="calc_zt"):
        s_si = to_si(s_zt_val, s_zt_unit, "seebeck")
        sigma_si = to_si(sigma_zt_val, sigma_zt_unit, "conductivity")
        t_si = to_si(t_zt_val, t_zt_unit, "temperature")
        k_si = to_si(kappa_zt_val, kappa_zt_unit, "thermal_conductivity")

        temp_error = validate_temperature_k(t_si)
        kappa_error = validate_thermal_conductivity(k_si)

        if temp_error:
            st.error(temp_error)
        if kappa_error:
            st.error(kappa_error)

        if not temp_error and not kappa_error:
            zt_val = zt_dimensionless(s_si, sigma_si, t_si, k_si)
            st.success(f"zT = {zt_val:.6g}")

with tab_batch:
    st.header("Batch CSV Processor")
    upload = st.file_uploader("Upload CSV", type=["csv"])

    if upload is not None:
        df = pd.read_csv(upload)
        st.write("Preview")
        st.dataframe(df.head(), use_container_width=True)

        mode = st.selectbox("Batch mode", ["Convert units", "Calculate PF", "Calculate zT"])
        columns = df.columns.tolist()

        processed_df = None

        if mode == "Convert units":
            source_col = st.selectbox("Source column", columns)
            property_label = st.selectbox(
                "Property", list(PROPERTY_LABEL_TO_KEY.keys()), key="batch_prop"
            )
            property_key = PROPERTY_LABEL_TO_KEY[property_label]
            source_unit = st.selectbox("Input unit", PROPERTY_UNITS[property_key], key="batch_unit")

            if st.button("Run batch convert"):
                processed_df = _process_batch_convert(df, source_col, source_unit, property_key)

        elif mode == "Calculate PF":
            seebeck_col = st.selectbox("Seebeck column", columns)
            seebeck_unit = st.selectbox("Seebeck unit", PROPERTY_UNITS["seebeck"], key="bpf_s_u")
            sigma_col = st.selectbox("Conductivity column", columns)
            sigma_unit = st.selectbox(
                "Conductivity unit", PROPERTY_UNITS["conductivity"], key="bpf_sig_u"
            )

            if st.button("Run batch PF"):
                st.info("Reminder: PF uses S², so Seebeck sign does not affect PF magnitude.")
                processed_df = _process_batch_pf(
                    df,
                    seebeck_col,
                    seebeck_unit,
                    sigma_col,
                    sigma_unit,
                )

        else:
            seebeck_col = st.selectbox("Seebeck column", columns, key="bzt_s")
            seebeck_unit = st.selectbox("Seebeck unit", PROPERTY_UNITS["seebeck"], key="bzt_s_u")
            sigma_col = st.selectbox("Conductivity column", columns, key="bzt_sig")
            sigma_unit = st.selectbox(
                "Conductivity unit", PROPERTY_UNITS["conductivity"], key="bzt_sig_u"
            )
            temp_col = st.selectbox("Temperature column", columns)
            temp_unit = st.selectbox("Temperature unit", PROPERTY_UNITS["temperature"])
            kappa_col = st.selectbox("Thermal conductivity column", columns)
            kappa_unit = st.selectbox(
                "Thermal conductivity unit", PROPERTY_UNITS["thermal_conductivity"]
            )

            if st.button("Run batch zT"):
                processed_df = _process_batch_zt(
                    df,
                    seebeck_col,
                    seebeck_unit,
                    sigma_col,
                    sigma_unit,
                    temp_col,
                    temp_unit,
                    kappa_col,
                    kappa_unit,
                )

        if processed_df is not None:
            st.subheader("Processed output")
            st.dataframe(processed_df, use_container_width=True)

            buffer = io.StringIO()
            processed_df.to_csv(buffer, index=False)
            st.download_button(
                label="Download processed CSV",
                data=buffer.getvalue(),
                file_name="processed_te_data.csv",
                mime="text/csv",
            )
