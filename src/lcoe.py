"""
Core LCOE calculation, sensitivity analysis, and default parameter data for
the LCOE Optimization Tool.

Validated against IESO's March 2024 published LCOE figures (see Notebook 1) —
formula reproduces IESO's own numbers within 0.05 $/MWh when using
technology-specific discount rates and a 25-year project life (see Notebook 2).
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go


def capital_recovery_factor(discount_rate: float, project_life: int) -> float:
    r = discount_rate
    n = project_life
    return (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def calculate_lcoe(capex: float, discount_rate: float, project_life: int, fixed_om: float,
                    capacity_factor: float, variable_om: float = 0, fuel_cost: float = 0) -> float:
    crf = capital_recovery_factor(discount_rate, project_life)
    aep_net_per_kw = (capacity_factor * 8760) / 1000
    lcoe = (capex * crf + fixed_om) / aep_net_per_kw + variable_om + fuel_cost
    return lcoe


def build_param_ranges(base_row: pd.Series) -> dict:
    ranges = {
        "CapEx": (base_row["CapEx"] * 0.85, base_row["CapEx"] * 1.15),
        "FixedOM": (base_row["FixedOM"] * 0.70, base_row["FixedOM"] * 1.30),
        "CapacityFactor": (max(base_row["CapacityFactor"] - 0.05, 0.01), base_row["CapacityFactor"] + 0.05),
        "DiscountRate": (max(base_row["DiscountRate"] - 0.01, 0.005), base_row["DiscountRate"] + 0.01),
        "ProjectLife": (20, 30),
    }
    if base_row["FuelCost"] > 0:
        ranges["FuelCost"] = (base_row["FuelCost"] * 0.60, base_row["FuelCost"] * 1.40)
    return ranges


def sensitivity_analysis(base_row: pd.Series, param_ranges: dict) -> pd.DataFrame:
    results = []
    arg_map = {
        "CapEx": "capex", "FixedOM": "fixed_om", "CapacityFactor": "capacity_factor",
        "DiscountRate": "discount_rate", "ProjectLife": "project_life", "FuelCost": "fuel_cost"
    }
    for param, (low_val, high_val) in param_ranges.items():
        for label, val in [("Low", low_val), ("High", high_val)]:
            test_params = {
                "capex": base_row["CapEx"],
                "discount_rate": base_row["DiscountRate"],
                "project_life": base_row["ProjectLife"],
                "fixed_om": base_row["FixedOM"],
                "capacity_factor": base_row["CapacityFactor"],
                "variable_om": base_row["VarOM"],
                "fuel_cost": base_row["FuelCost"],
            }
            test_params[arg_map[param]] = val
            lcoe = calculate_lcoe(**test_params)
            results.append({"Parameter": param, "Level": label, "LCOE": lcoe})

    df = pd.DataFrame(results)
    pivoted = df.pivot(index="Parameter", columns="Level", values="LCOE")
    pivoted["Swing"] = (pivoted["High"] - pivoted["Low"]).abs()
    return pivoted.sort_values("Swing", ascending=True)


def plot_tornado(tornado_data: pd.DataFrame, technology_name: str, base_lcoe: float,
                  x_range: tuple = None, label_color: str = "#1a1a1a",
                  bar_color: str = "#2E5EAA", bar_line_color: str = "#1a3a6e") -> go.Figure:
    """
    label_color, bar_color, bar_line_color are themeable so the same function
    reads correctly on both a light background (notebooks) and a dark
    background (the Streamlit app) — a fixed dark label color was previously
    nearly invisible against the app's dark theme.
    """
    data = tornado_data.sort_values("Swing", ascending=True)
    fig = go.Figure()

    for param, row in data.iterrows():
        low, high = row["Low"], row["High"]
        fig.add_trace(go.Bar(
            y=[param], x=[high - low], base=[low], orientation="h",
            marker=dict(color=bar_color, line=dict(color=bar_line_color, width=1)),
            hovertemplate=f"<b>{param}</b><br>Low: ${low:.1f}/MWh<br>High: ${high:.1f}/MWh<br>Swing: ${row['Swing']:.1f}/MWh<extra></extra>",
            showlegend=False
        ))
        fig.add_annotation(x=low, y=param, text=f"${low:.0f}", showarrow=False,
                            xanchor="right", xshift=-12, font=dict(size=12, color=label_color))
        fig.add_annotation(x=high, y=param, text=f"${high:.0f}", showarrow=False,
                            xanchor="left", xshift=12, font=dict(size=12, color=label_color))

    fig.add_vline(x=base_lcoe, line_dash="dash", line_color="#F2B705", line_width=2,
                   annotation_text=f"Base LCOE = ${base_lcoe:.0f}/MWh", annotation_position="top",
                   annotation_font=dict(color=label_color))

    if x_range is not None:
        final_range = x_range
    else:
        # Wider padding than before (18%, up from 8%) so labels never crowd
        # the plot edges, especially for parameters with large swings
        x_min, x_max = data["Low"].min(), data["High"].max()
        padding = (x_max - x_min) * 0.18
        final_range = [x_min - padding, x_max + padding]

    fig.update_layout(
        title=f"Sensitivity Analysis — {technology_name}",
        xaxis_title="LCOE ($/MWh)",
        xaxis=dict(gridcolor="#e5e5e5", range=final_range, automargin=True),
        height=420,
        margin=dict(l=40, r=40, t=60, b=10),
        plot_bgcolor="white",
        bargap=0.35
    )
    return fig


def load_defaults(path: str = "data/lcoe_defaults.csv") -> pd.DataFrame:
    return pd.read_csv(path)