"""
LCOE Optimization Tool — Streamlit app.

Calculates and compares the Levelized Cost of Energy (LCOE) for Solar, Wind,
and Natural Gas across Nova Scotia, Ontario, and Alberta. Formula validated
against IESO's published 2024 figures (see notebooks/01_lcoe_fundamentals.ipynb).
All parameters are editable — defaults are sourced/estimated starting points,
not fixed truths (see notebooks for full sourcing detail).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys

sys.path.append("src")
from lcoe import calculate_lcoe, build_param_ranges, sensitivity_analysis, plot_tornado, load_defaults

# ---------------------------------------------------------------
# Page config + styling
# ---------------------------------------------------------------
st.set_page_config(page_title="LCOE Optimization Tool — Canada", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0B1220; color: #E8EDF4; }
#MainMenu, footer, header { visibility: hidden; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; color: #E8EDF4 !important; }

/* Hero banner */
.hero {
    background: linear-gradient(135deg, #131B2E 0%, #0F1626 100%);
    border: 1px solid #24304A;
    border-radius: 14px;
    padding: 32px 36px;
    margin-bottom: 22px;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3.4rem;
    font-weight: 700;
    color: #E8EDF4;
    margin: 0 0 8px 0;
    display: flex;
    align-items: center;
    gap: 14px;
}
.hero-subtitle { color: #8593AD; font-size: 1rem; margin: 0 0 18px 0; }
.hero-definition {
    background: #0F1626;
    border-left: 3px solid #F2B705;
    border-radius: 6px;
    padding: 16px 20px;
    margin-bottom: 14px;
}
.hero-definition-label {
    font-family: 'JetBrains Mono', monospace;
    color: #F2B705;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}
.hero-definition-text { color: #C4CDE0; font-size: 0.98rem; line-height: 1.6; margin: 0; }
.hero-purpose { color: #C4CDE0; font-size: 0.95rem; line-height: 1.6; margin: 0; }

/* Technology cards */
.tech-card {
    background: #131B2E;
    border: 2px solid #24304A;
    border-radius: 12px;
    padding: 18px;
    text-align: center;
    transition: border-color 0.2s;
}
.tech-card-icon { width: 56px; height: 56px; margin: 0 auto 8px auto; }
.tech-card-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.05rem; color: #E8EDF4; }
.tech-card-lcoe { font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 700; margin-top: 6px; }

/* Metric cards */
div[data-testid="stMetric"] {
    background-color: #131B2E; border: 1px solid #24304A; border-radius: 10px; padding: 16px 18px;
}
div[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; color: #F2B705 !important; }
div[data-testid="stMetricLabel"] { color: #8593AD !important; }

/* Selectboxes and sliders */
div[data-baseweb="select"] > div { background-color: #131B2E !important; border-color: #24304A !important; border-radius: 8px !important; }

/* Section headers */
.section-header { display: flex; align-items: center; gap: 10px; margin: 8px 0 4px 0; }
.section-icon { width: 6px; height: 22px; background: #F2B705; border-radius: 3px; }
.section-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem; font-weight: 700; color: #E8EDF4; }

/* Divider */
.transmission-line {
    height: 2px; margin: 28px 0;
    background: repeating-linear-gradient(90deg, #F2B705 0px, #F2B705 8px, transparent 8px, transparent 16px);
    background-size: 32px 2px; animation: flow 1.2s linear infinite; opacity: 0.55;
}
@keyframes flow { from { background-position: 0 0; } to { background-position: 32px 0; } }

.source-tag {
    display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
    padding: 2px 8px; border-radius: 5px; margin-left: 8px;
}
.source-sourced { background: rgba(46, 158, 91, 0.15); color: #4CD97B; border: 1px solid #2E9E5B; }
.source-estimated { background: rgba(242, 183, 5, 0.15); color: #F2B705; border: 1px solid #F2B705; }

/* --- Animations for the title icon and technology graphics --- */

/* Title scale icon: gentle tilt back and forth, like weighing options */
.title-icon { display: inline-flex; width: 62px; height: 62px; flex-shrink: 0; }
.title-icon svg { width: 100%; height: 100%; animation: scale-tilt 3.5s ease-in-out infinite; transform-origin: 32px 20px; }
@keyframes scale-tilt {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(-6deg); }
    75% { transform: rotate(6deg); }
}

/* Wind turbine blades: continuous rotation around the hub */
.wind-blades { animation: spin 4s linear infinite; transform-origin: 32px 18px; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* Gas flame: flicker via subtle scale + opacity pulsing */
.gas-flame-outer { animation: flicker-outer 1.8s ease-in-out infinite; transform-origin: 32px 58px; }
.gas-flame-inner { animation: flicker-inner 1.3s ease-in-out infinite; transform-origin: 32px 50px; }
@keyframes flicker-outer {
    0%, 100% { transform: scale(1, 1); opacity: 0.9; }
    50% { transform: scale(1.04, 0.97); opacity: 1; }
}
@keyframes flicker-inner {
    0%, 100% { transform: scale(1, 1); opacity: 1; }
    50% { transform: scale(0.94, 1.05); opacity: 0.85; }
}

/* Solar: sun glint sweeps across the panel, rays pulse gently */
.solar-glint { animation: glint-move 3s ease-in-out infinite; }
@keyframes glint-move {
    0% { transform: translateX(-6px); opacity: 0; }
    50% { opacity: 0.9; }
    100% { transform: translateX(6px); opacity: 0; }
}
.solar-ray { animation: ray-pulse 2.2s ease-in-out infinite; transform-origin: 52px 8px; }
@keyframes ray-pulse {
    0%, 100% { opacity: 0.5; r: 3.5; }
    50% { opacity: 1; r: 5; }
}

/* Infographic flow strip */
.flow-strip { display: flex; align-items: center; justify-content: space-between; gap: 6px; margin: 4px 0 2px 0; }
.flow-step { flex: 1; text-align: center; }
.flow-step-icon { font-size: 1.6rem; }
.flow-step-label { color: #8593AD; font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; margin-top: 2px; }
.flow-arrow { color: #F2B705; font-size: 1.3rem; opacity: 0.7; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Custom SVG icons — solar panel, wind turbine, gas flame (all animated via CSS)
# ---------------------------------------------------------------
SOLAR_ICON = """
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect x="8" y="10" width="48" height="32" rx="2" fill="#1B2438" stroke="#F2B705" stroke-width="2"/>
  <line x1="8" y1="20" x2="56" y2="20" stroke="#F2B705" stroke-width="1.5"/>
  <line x1="8" y1="30" x2="56" y2="30" stroke="#F2B705" stroke-width="1.5"/>
  <line x1="20" y1="10" x2="20" y2="42" stroke="#F2B705" stroke-width="1.5"/>
  <line x1="32" y1="10" x2="32" y2="42" stroke="#F2B705" stroke-width="1.5"/>
  <line x1="44" y1="10" x2="44" y2="42" stroke="#F2B705" stroke-width="1.5"/>
  <line x1="32" y1="42" x2="24" y2="56" stroke="#8593AD" stroke-width="3" stroke-linecap="round"/>
  <line x1="32" y1="42" x2="40" y2="56" stroke="#8593AD" stroke-width="3" stroke-linecap="round"/>
  <rect class="solar-glint" x="10" y="10" width="6" height="32" fill="#FFFFFF" opacity="0"/>
  <circle class="solar-ray" cx="52" cy="8" r="4" fill="#F2B705"/>
</svg>
"""

WIND_ICON = """
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <line x1="32" y1="58" x2="32" y2="20" stroke="#8593AD" stroke-width="3" stroke-linecap="round"/>
  <circle cx="32" cy="18" r="3" fill="#E8EDF4"/>
  <g class="wind-blades" stroke="#2DD4BF" stroke-width="3" stroke-linecap="round" fill="none">
    <path d="M32 18 L 52 10 Q 56 14 52 20 Z" fill="#2DD4BF" opacity="0.85"/>
    <path d="M32 18 L 16 32 Q 12 28 16 22 Z" fill="#2DD4BF" opacity="0.85"/>
    <path d="M32 18 L 40 44 Q 34 46 30 42 Z" fill="#2DD4BF" opacity="0.85"/>
  </g>
</svg>
"""

GAS_ICON = """
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <path class="gas-flame-outer" d="M32 6 C 24 20, 40 24, 34 36 C 44 30, 48 44, 32 58 C 16 44, 20 30, 30 36 C 24 24, 40 20, 32 6 Z"
        fill="#E8622C" opacity="0.9"/>
  <path class="gas-flame-inner" d="M32 22 C 28 30, 36 32, 33 38 C 38 35, 40 42, 32 50 C 24 42, 26 35, 30 38 C 27 32, 35 30, 32 22 Z"
        fill="#F2B705"/>
</svg>
"""

# Title icon — a balance scale, representing LCOE's role in weighing cost options
SCALE_ICON = """
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <line x1="32" y1="8" x2="32" y2="50" stroke="#F2B705" stroke-width="3" stroke-linecap="round"/>
  <line x1="10" y1="16" x2="54" y2="16" stroke="#F2B705" stroke-width="3" stroke-linecap="round"/>
  <circle cx="32" cy="8" r="3.5" fill="#F2B705"/>
  <line x1="10" y1="16" x2="10" y2="30" stroke="#8593AD" stroke-width="2"/>
  <path d="M2 30 Q10 40 18 30 Z" fill="none" stroke="#2DD4BF" stroke-width="2.5" stroke-linejoin="round"/>
  <line x1="54" y1="16" x2="54" y2="30" stroke="#8593AD" stroke-width="2"/>
  <path d="M46 30 Q54 40 62 30 Z" fill="none" stroke="#E8622C" stroke-width="2.5" stroke-linejoin="round"/>
  <rect x="22" y="50" width="20" height="6" rx="1.5" fill="#8593AD"/>
  <rect x="28" y="52" width="8" height="10" fill="#8593AD"/>
  <rect x="20" y="60" width="24" height="3" rx="1.5" fill="#8593AD"/>
</svg>
"""

# ---------------------------------------------------------------
# Data + config
# ---------------------------------------------------------------
PROVINCE_NAMES = {
    "ON": "Ontario", "QC": "Quebec", "BC": "British Columbia", "AB": "Alberta",
    "MB": "Manitoba", "SK": "Saskatchewan", "NS": "Nova Scotia",
    "NB": "New Brunswick", "NL": "Newfoundland and Labrador", "PE": "Prince Edward Island"
}
TECH_ICONS = {"Solar": SOLAR_ICON, "Wind": WIND_ICON, "Natural Gas": GAS_ICON}
TECH_COLORS = {"Solar": "#F2B705", "Wind": "#2DD4BF", "Natural Gas": "#E8622C"}

# ---------------------------------------------------------------
# Hero — title, LCOE definition, purpose, "how it's calculated" infographic
# ---------------------------------------------------------------
st.markdown(f"""
<div class="hero">
    <p class="hero-title"><span class="title-icon">{SCALE_ICON}</span>LCOE Optimization Tool</p>
    <p class="hero-subtitle">Comparing the true cost of Solar, Wind, and Natural Gas across Canada</p>
    <div class="hero-definition">
        <div class="hero-definition-label">What is LCOE?</div>
        <p class="hero-definition-text">
            The <strong>Levelized Cost of Energy (LCOE)</strong> is the average cost, in dollars per
            megawatt-hour, of building and operating a power plant over its entire lifetime, divided by
            the total electricity it produces. It collapses very different cost and output profiles —
            a cheap-to-build but low-output solar farm, versus an expensive nuclear plant that runs for
            decades — into one comparable number, expressed the same way for every technology.
        </p>
        <div class="flow-strip">
            <div class="flow-step"><div class="flow-step-icon">🏗️</div><div class="flow-step-label">CAPITAL + O&M COST</div></div>
            <div class="flow-arrow">÷</div>
            <div class="flow-step"><div class="flow-step-icon">⚡</div><div class="flow-step-label">ENERGY PRODUCED</div></div>
            <div class="flow-arrow">=</div>
            <div class="flow-step"><div class="flow-step-icon">💲</div><div class="flow-step-label">LCOE ($/MWh)</div></div>
        </div>
    </div>
    <p class="hero-purpose">
        <strong>Why it matters:</strong> LCOE is the first number an energy company calculates before
        deciding whether a project is worth building at all. Get it wrong, and a "cheap" project can
        turn out to be the expensive one once real-world capacity factors and financing costs are
        accounted for. This tool lets you build that number yourself — pick a province and technology,
        adjust the real inputs (capital cost, O&M, capacity factor, financing), and see exactly how each
        one moves the final cost, backed by a formula validated against Ontario's own official published figures.
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Load data
# ---------------------------------------------------------------
defaults = load_defaults("data/lcoe_defaults.csv")

# ---------------------------------------------------------------
# Province selector
# ---------------------------------------------------------------
province_code = st.selectbox(
    "Province", options=list(PROVINCE_NAMES.keys()),
    format_func=lambda x: PROVINCE_NAMES[x], index=0,
    help="Capital cost and financing terms are treated as consistent across provinces (equipment and "
         "financing markets are largely national). Capacity factor — the parameter that varies most by "
         "region — is directly sourced for Ontario (IESO 2024) and reasoned-estimate for NS/AB."
)

# ---------------------------------------------------------------
# Technology comparison cards (all 3, at a glance)
# ---------------------------------------------------------------
header_col, toggle_col = st.columns([3, 1])
with header_col:
    st.markdown(f"""
    <div class="section-header">
        <div class="section-icon"></div>
        <div class="section-title">At a glance — {PROVINCE_NAMES[province_code]}</div>
    </div>
    """, unsafe_allow_html=True)
with toggle_col:
    unit_choice = st.radio(
        "Units", options=["$/MWh", "$/kWh"], horizontal=True, label_visibility="collapsed",
        help="Switch between $/MWh (standard for utility-scale comparisons) and $/kWh (more familiar "
             "from residential electricity bills). Same number, different scale: divide by 1,000 to go "
             "from $/MWh to $/kWh."
    )

card_cols = st.columns(3)
province_rows = defaults[defaults["Province"] == province_code].set_index("Technology")

for col, tech in zip(card_cols, ["Solar", "Wind", "Natural Gas"]):
    row = province_rows.loc[tech]
    if unit_choice == "$/MWh":
        display_value = f"${row['LCOE']:.0f}"
        display_unit = "/MWh"
    else:
        # $/kWh = $/MWh / 1000 — small numbers need more decimal places to stay meaningful
        display_value = f"${row['LCOE'] / 1000:.3f}"
        display_unit = "/kWh"
    with col:
        st.markdown(f"""
        <div class="tech-card">
            <div class="tech-card-icon">{TECH_ICONS[tech]}</div>
            <div class="tech-card-title">{tech}</div>
            <div class="tech-card-lcoe" style="color: {TECH_COLORS[tech]};">{display_value}<span style="font-size:0.9rem; color:#8593AD;">{display_unit}</span></div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="transmission-line"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------
# Technology selector + editable parameters
# ---------------------------------------------------------------
st.markdown("""
<div class="section-header">
    <div class="section-icon"></div>
    <div class="section-title">Build your own scenario</div>
</div>
""", unsafe_allow_html=True)

technology = st.radio("Technology", options=["Solar", "Wind", "Natural Gas"], horizontal=True,
                       help="Select a technology to adjust its parameters below.")

base_row = province_rows.loc[technology]
is_sourced = base_row["Source"].startswith("IESO")
tag_class = "source-sourced" if is_sourced else "source-estimated"
tag_text = "IESO 2024 — Sourced" if is_sourced else "Regionally Estimated"
st.markdown(f'<span class="source-tag {tag_class}">{tag_text}</span>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    capex = st.slider("Capital Expenditure ($/kW)", min_value=int(base_row["CapEx"] * 0.5),
                       max_value=int(base_row["CapEx"] * 1.8), value=int(base_row["CapEx"]), step=10,
                       help="CapEx: the upfront cost to build the plant, per kW of capacity. The single "
                            "largest input for most technologies.")
    fixed_om = st.slider("Fixed O&M ($/kW/yr)", min_value=int(base_row["FixedOM"] * 0.3),
                          max_value=int(base_row["FixedOM"] * 2.5), value=int(base_row["FixedOM"]), step=1,
                          help="Fixed O&M: annual operating and maintenance cost per kW of capacity, "
                               "independent of how much energy is actually produced.")
    capacity_factor_pct = st.slider("Capacity Factor (%)", min_value=1, max_value=95,
                                     value=int(base_row["CapacityFactor"] * 100), step=1,
                                     help="Capacity Factor: what fraction of the year the plant actually "
                                          "produces at its rated capacity. The single most influential "
                                          "input for solar and wind.")
with col2:
    discount_rate_pct = st.slider("Discount Rate (%)", min_value=1.0, max_value=12.0,
                                   value=round(base_row["DiscountRate"] * 100, 2), step=0.1,
                                   help="Discount Rate: the real cost of financing the project — higher "
                                        "rates mean investors demand more return, raising LCOE.")
    project_life = st.slider("Project Life (years)", min_value=10, max_value=40,
                              value=int(base_row["ProjectLife"]), step=1,
                              help="Project Life: how many years the plant is expected to operate. Longer "
                                   "life spreads capital cost over more energy produced, lowering LCOE.")
    if technology == "Natural Gas":
        fuel_cost = st.slider("Fuel Cost ($/MWh)", min_value=5, max_value=100,
                               value=int(base_row["FuelCost"]), step=1,
                               help="Fuel Cost: the price of natural gas per MWh generated. Gas is the "
                                    "only technology here with a meaningful fuel cost — solar and wind "
                                    "have none.")
        variable_om = base_row["VarOM"]
    else:
        fuel_cost = 0
        variable_om = 0

# ---------------------------------------------------------------
# Calculate and display result
# ---------------------------------------------------------------
result_lcoe = calculate_lcoe(
    capex=capex, discount_rate=discount_rate_pct / 100, project_life=project_life,
    fixed_om=fixed_om, capacity_factor=capacity_factor_pct / 100,
    variable_om=variable_om, fuel_cost=fuel_cost
)

st.markdown('<div class="transmission-line"></div>', unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("Your Scenario LCOE", f"${result_lcoe:.1f}/MWh",
          help="The Levelized Cost of Energy for the parameters you've set above.")
m2.metric(f"{PROVINCE_NAMES[province_code]} Default LCOE", f"${base_row['LCOE']:.1f}/MWh",
          help="The LCOE using this technology's default parameters for the selected province.")
diff = result_lcoe - base_row["LCOE"]
m3.metric("Difference from Default", f"${diff:+.1f}/MWh",
          help="How much your adjustments moved the result compared to the default scenario.")

# ---------------------------------------------------------------
# Sensitivity tornado chart
# ---------------------------------------------------------------
st.markdown('<div class="transmission-line"></div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="section-header">
    <div class="section-icon"></div>
    <div class="section-title">Sensitivity Analysis — {technology}</div>
</div>
""", unsafe_allow_html=True)
st.caption("Which input matters most? Each bar shows how far LCOE swings when that parameter alone is varied, holding all others at their default.")

sensitivity_row = base_row.copy()
ranges = build_param_ranges(sensitivity_row)
tornado_data = sensitivity_analysis(sensitivity_row, ranges)
fig = plot_tornado(
    tornado_data, f"{PROVINCE_NAMES[province_code]} {technology}", base_row["LCOE"],
    label_color="#E8EDF4", bar_color="#2E5EAA", bar_line_color="#5B85C9"
)
fig.update_layout(paper_bgcolor="#0B1220", plot_bgcolor="#131B2E", font_color="#E8EDF4")
fig.update_xaxes(gridcolor="#1E2A42")
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------
# Cross-technology comparison chart
# ---------------------------------------------------------------
st.markdown('<div class="transmission-line"></div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="section-header">
    <div class="section-icon"></div>
    <div class="section-title">Technology Comparison — {PROVINCE_NAMES[province_code]}</div>
</div>
""", unsafe_allow_html=True)

compare_fig = go.Figure()
for tech in ["Solar", "Wind", "Natural Gas"]:
    row = province_rows.loc[tech]
    compare_fig.add_trace(go.Bar(
        x=[tech], y=[row["LCOE"]], marker_color=TECH_COLORS[tech],
        text=[f"${row['LCOE']:.0f}"], textposition="outside",
        hovertemplate=f"<b>{tech}</b><br>LCOE: ${row['LCOE']:.1f}/MWh<extra></extra>",
        showlegend=False
    ))
compare_fig.update_layout(
    yaxis_title="LCOE ($/MWh)", height=380,
    paper_bgcolor="#0B1220", plot_bgcolor="#131B2E", font_color="#E8EDF4",
    yaxis=dict(gridcolor="#1E2A42"), margin=dict(t=20, l=10, r=10, b=10)
)
st.plotly_chart(compare_fig, use_container_width=True)

# ---------------------------------------------------------------
# Footer
# ---------------------------------------------------------------
st.markdown('<div class="transmission-line"></div>', unsafe_allow_html=True)
st.caption(
    "Formula validated against IESO's March 2024 Resource Costs and Trends report (Ontario). "
    "Nova Scotia and Alberta capacity factors are reasoned regional estimates, clearly flagged above — "
    "see the project notebooks for full sourcing methodology and formula derivation."
)
st.markdown(
    "<p style='color: #8593AD; font-size: 0.82rem; margin-top: 8px;'>"
    "Built by Tendekai Mugomba — "
    "<a href='https://www.linkedin.com/in/YOUR-LINKEDIN-HANDLE' style='color: #F2B705;'>LinkedIn</a> · "
    "<a href='https://github.com/tmugomba' style='color: #F2B705;'>GitHub</a>"
    "</p>",
    unsafe_allow_html=True
)