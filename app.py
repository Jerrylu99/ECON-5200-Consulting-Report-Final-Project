# app.py — ECON 5200 Final Project Dashboard
# Deploy: streamlit run app.py
# Requirements: streamlit, plotly, numpy, pandas

import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Minimum Wage & Teen Employment | DML Analysis",
    layout="wide",
    page_icon="🔬",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .main-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.7rem;
        font-weight: 600;
        color: #0f2942;
        letter-spacing: -0.5px;
        margin-bottom: 0;
    }
    .subtitle {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 0.9rem;
        color: #5a7a9a;
        font-weight: 300;
        margin-top: 2px;
    }
    .section-header {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #5a7a9a;
        border-bottom: 1px solid #dce8f5;
        padding-bottom: 6px;
        margin-bottom: 12px;
    }
    .result-card {
        background: #f5f9ff;
        border-left: 3px solid #1a6fc4;
        border-radius: 4px;
        padding: 12px 16px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.88rem;
        color: #0f2942;
        margin: 8px 0;
    }
    .warning-card {
        background: #fff8f0;
        border-left: 3px solid #e07020;
        border-radius: 4px;
        padding: 12px 16px;
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 0.88rem;
        color: #7a3a00;
        margin: 8px 0;
    }
    .metric-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #5a7a9a;
    }
    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.8rem;
        font-weight: 600;
        color: #0f2942;
        line-height: 1.1;
    }
    .metric-value.negative { color: #c0392b; }
    .metric-value.positive { color: #1a7a3c; }
    .metric-value.neutral  { color: #1a6fc4; }
    .stExpander { border: 1px solid #dce8f5 !important; border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)

# ── Pre-computed DML results ──────────────────────────────────
BASELINE_ATE = -1.2822   # DML (GBM) estimate, pp per log-point MW increase
BASELINE_SE  =  0.3652   # robust standard error
TRUE_EFFECT  = -1.50     # embedded DGP true value (simulation ground truth)
OLS_EST      = -0.31     # naive OLS benchmark
LASSO_ATE    = -1.31     # DML Lasso robustness check

# ── Header ────────────────────────────────────────────────────
st.markdown('<p class="main-title">Does Minimum Wage Reduce Teen Employment?</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">ECON 5200 | Double Machine Learning (DML) Analysis | State Panel 2000–2021 | N = 1,100</p>', unsafe_allow_html=True)
st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.markdown("### Scenario Controls")
st.sidebar.markdown("Simulate counterfactual minimum wage changes and explore effect uncertainty.")

mw_change_pct = st.sidebar.slider(
    "Minimum Wage Change (%)",
    min_value=-40, max_value=100, value=10, step=5,
    help="Simulate a percentage change in the state minimum wage."
)
confidence_level = st.sidebar.selectbox(
    "Confidence Level", [90, 95, 99], index=1
)
show_ols = st.sidebar.checkbox("Show OLS benchmark on chart", value=True)
show_true = st.sidebar.checkbox("Show DGP true effect on chart", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Reference Estimates**")
st.sidebar.markdown(f"- Naive OLS: `{OLS_EST:.2f}` pp *(biased)*")
st.sidebar.markdown(f"- DML (GBM): `{BASELINE_ATE:.2f}` pp *(primary)*")
st.sidebar.markdown(f"- DML (Lasso): `{LASSO_ATE:.2f}` pp *(robust)*")
st.sidebar.markdown(f"- DGP True: `{TRUE_EFFECT:.2f}` pp *(benchmark)*")

# ── Scenario Computation ──────────────────────────────────────
z_map = {90: 1.645, 95: 1.96, 99: 2.576}
z = z_map[confidence_level]

delta_log_mw = np.log(1 + mw_change_pct / 100) if mw_change_pct > -100 else -np.inf
scenario_ate = BASELINE_ATE * delta_log_mw
scenario_se  = abs(BASELINE_SE * delta_log_mw)
ci_lo = scenario_ate - z * scenario_se
ci_hi = scenario_ate + z * scenario_se

# ── Key Metrics Row ───────────────────────────────────────────
st.markdown('<p class="section-header">Scenario Results</p>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

def render_metric(col, label, value, fmt, css_class="neutral"):
    col.markdown(
        f'<p class="metric-label">{label}</p>'
        f'<p class="metric-value {css_class}">{fmt.format(value)}</p>',
        unsafe_allow_html=True
    )

render_metric(col1, "MW Change",          mw_change_pct,  "{:+d}%",    "neutral")
ate_class = "negative" if scenario_ate < -0.01 else ("positive" if scenario_ate > 0.01 else "neutral")
render_metric(col2, "Estimated ΔEmp (pp)", scenario_ate,   "{:+.3f}",   ate_class)
render_metric(col3, f"{confidence_level}% CI Lower",  ci_lo, "{:+.3f}", "negative")
render_metric(col4, f"{confidence_level}% CI Upper",  ci_hi, "{:+.3f}", ate_class)
render_metric(col5, "Implied ΔJobs (mn teens)", scenario_ate * 0.3, "{:+.2f}", ate_class)

# ── Interpretation box ─────────────────────────────────────────
if mw_change_pct != 0:
    direction = "reduce" if scenario_ate < 0 else "increase"
    nat_effect = scenario_ate * 0.3  # ~30mn US teens
    st.markdown(
        f'<div class="result-card">A <strong>{mw_change_pct:+d}%</strong> change in minimum wage is estimated to '
        f'<strong>{direction}</strong> the teen employment rate by <strong>{abs(scenario_ate):.3f} pp</strong> '
        f'({confidence_level}% CI: [{ci_lo:.3f}, {ci_hi:.3f}] pp). '
        f'At the national level (~30M teens), this corresponds to approximately '
        f'<strong>{abs(nat_effect):.2f} million</strong> {"fewer" if scenario_ate < 0 else "additional"} employed teenagers.</div>',
        unsafe_allow_html=True
    )

st.markdown("---")

# ── Main Chart ────────────────────────────────────────────────
st.markdown('<p class="section-header">Effect vs. Minimum Wage Change (What-If Curve)</p>', unsafe_allow_html=True)

mw_range   = np.arange(-40, 101, 1)
delta_logs = np.where(mw_range > -100, np.log(1 + mw_range / 100), np.nan)
ates_curve = BASELINE_ATE * delta_logs
ses_curve  = np.abs(BASELINE_SE * delta_logs)

fig = go.Figure()

# CI band
fig.add_trace(go.Scatter(
    x=mw_range, y=ates_curve + z * ses_curve,
    mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"
))
fig.add_trace(go.Scatter(
    x=mw_range, y=ates_curve - z * ses_curve,
    mode="lines", line=dict(width=0),
    fill="tonexty", fillcolor="rgba(26,111,196,0.12)",
    name=f"{confidence_level}% Confidence Band", hoverinfo="skip"
))

# DML primary
fig.add_trace(go.Scatter(
    x=mw_range, y=ates_curve,
    mode="lines", line=dict(color="#1a6fc4", width=2.5),
    name="DML Estimate (GBM)",
    hovertemplate="MW Change: %{x:+d}%<br>Effect: %{y:.3f} pp<extra></extra>"
))

# OLS benchmark
if show_ols:
    ols_curve = OLS_EST * delta_logs
    fig.add_trace(go.Scatter(
        x=mw_range, y=ols_curve,
        mode="lines", line=dict(color="#e07020", width=1.5, dash="dot"),
        name="Naive OLS (biased benchmark)",
        hovertemplate="MW Change: %{x:+d}%<br>OLS: %{y:.3f} pp<extra></extra>"
    ))

# True effect
if show_true:
    true_curve = TRUE_EFFECT * delta_logs
    fig.add_trace(go.Scatter(
        x=mw_range, y=true_curve,
        mode="lines", line=dict(color="#2ecc71", width=1.5, dash="dash"),
        name="DGP True Effect (simulation)",
        hovertemplate="MW Change: %{x:+d}%<br>True: %{y:.3f} pp<extra></extra>"
    ))

# Current scenario marker
if mw_change_pct in mw_range:
    fig.add_vline(
        x=mw_change_pct, line_dash="dash", line_color="#c0392b", line_width=1.2,
        annotation_text=f"  Scenario: {mw_change_pct:+d}%",
        annotation_font=dict(color="#c0392b", size=11)
    )

fig.add_hline(y=0, line_color="#0f2942", line_width=0.8, opacity=0.3)

fig.update_layout(
    xaxis_title="Minimum Wage Change (%)",
    yaxis_title="Δ Teen Employment Rate (percentage points)",
    template="plotly_white",
    height=420,
    font=dict(family="IBM Plex Sans, sans-serif", size=12, color="#0f2942"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    margin=dict(l=0, r=10, t=40, b=0),
    xaxis=dict(gridcolor="#eef3fa", zeroline=False),
    yaxis=dict(gridcolor="#eef3fa", zeroline=False),
    plot_bgcolor="#fafcff",
    paper_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(fig, use_container_width=True)

# ── Estimator Comparison Chart ─────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-header">Estimator Comparison: Bias Correction via DML</p>', unsafe_allow_html=True)

methods     = ["Naive OLS", "DML (GBM)", "DML (Lasso)", "DGP True Effect"]
estimates   = [OLS_EST, BASELINE_ATE, LASSO_ATE, TRUE_EFFECT]
ci_lowers   = [-0.58,   -2.00,        -2.04,         TRUE_EFFECT]
ci_uppers   = [-0.04,   -0.57,        -0.58,         TRUE_EFFECT]
colors      = ["#e07020", "#1a6fc4", "#1a6fc4", "#2ecc71"]
statuses    = ["⚠ Biased (upward, ~80%)", "✓ Causal estimate", "✓ Robust check", "★ Ground truth"]

fig2 = go.Figure()

# CI error bars
for i, (m, est, lo, hi, col) in enumerate(zip(methods, estimates, ci_lowers, ci_uppers, colors)):
    if m != "DGP True Effect":
        fig2.add_trace(go.Scatter(
            x=[lo, hi], y=[m, m],
            mode="lines", line=dict(color=col, width=2),
            showlegend=False, hoverinfo="skip"
        ))
        # CI caps
        for x_val in [lo, hi]:
            fig2.add_trace(go.Scatter(
                x=[x_val, x_val], y=[i - 0.12, i + 0.12],
                mode="lines", line=dict(color=col, width=2),
                showlegend=False, hoverinfo="skip",
                yaxis="y"
            ))

# Point estimates
fig2.add_trace(go.Scatter(
    x=estimates,
    y=methods,
    mode="markers+text",
    marker=dict(color=colors, size=11, symbol=["diamond", "circle", "circle", "star"],
                line=dict(width=1.5, color="white")),
    text=[f" {v:.2f} pp  {s}" for v, s in zip(estimates, statuses)],
    textposition="middle right",
    textfont=dict(size=11, family="IBM Plex Mono"),
    showlegend=False,
    hovertemplate="%{y}: %{x:.3f} pp<extra></extra>"
))

fig2.add_vline(x=0, line_color="#0f2942", line_width=0.8, opacity=0.3)

fig2.update_layout(
    xaxis_title="Estimated Effect on Teen Employment Rate (pp per 10 log-pt MW increase)",
    template="plotly_white",
    height=260,
    font=dict(family="IBM Plex Sans, sans-serif", size=12, color="#0f2942"),
    margin=dict(l=100, r=200, t=20, b=40),
    xaxis=dict(gridcolor="#eef3fa", range=[-2.8, 0.5]),
    yaxis=dict(gridcolor="rgba(0,0,0,0)"),
    plot_bgcolor="#fafcff",
    paper_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown(
    '<div class="warning-card">'
    '⚠ <strong>Bias note:</strong> The naive OLS estimate (−0.31 pp) is attenuated ~80% toward zero relative to '
    'the DML estimate (−1.28 pp) due to <em>positive confounding</em>: states that adopt higher minimum wages '
    'tend to be economically stronger, which independently sustains teen employment. DML partials out this '
    'variation via cross-fitted ML residuals, recovering an estimate close to the known true effect (−1.50 pp).'
    '</div>',
    unsafe_allow_html=True
)

# ── Counterfactual ─────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-header">Policy Counterfactual: Minimum Wage Doubled (+100%)</p>', unsafe_allow_html=True)

delta_double = np.log(2)
cf_ate = BASELINE_ATE * delta_double
cf_se  = abs(BASELINE_SE * delta_double)
cf_lo  = cf_ate - z * cf_se
cf_hi  = cf_ate + z * cf_se
cf_nat = cf_ate * 0.3  # millions of teens

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(
        f'<div class="result-card">'
        f'<strong>Estimated effect:</strong> {cf_ate:+.3f} pp<br>'
        f'<strong>{confidence_level}% CI:</strong> [{cf_lo:.3f}, {cf_hi:.3f}] pp<br>'
        f'<strong>Implied national impact:</strong> ≈ {abs(cf_nat):.2f} million fewer employed teens'
        f'</div>',
        unsafe_allow_html=True
    )
with col_b:
    st.markdown(
        '<div class="warning-card">'
        '<strong>Interpretation caveat:</strong> This counterfactual extrapolates well beyond the '
        'support of the data (observed log MW range: ~1.64–2.71). Linear scaling of the DML ATE '
        'assumes a constant effect per log-point — a strong assumption at extreme values. '
        'Treat as an illustrative upper bound, not a precise forecast.'
        '</div>',
        unsafe_allow_html=True
    )

# ── Methodology Expander ───────────────────────────────────────
st.markdown("---")
with st.expander("📋 Methodology & Identification Strategy"):
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("""
**Identification Strategy**

Double Machine Learning (DML) — Partially Linear Regression (Chernozhukov et al. 2018).

Structural equations:
- `Y = θ₀·D + g₀(W) + ε`
- `D = m₀(W) + V`

**Key Assumption — Conditional Independence:**
After conditioning on observed confounders W, residual minimum wage variation V is uncorrelated with unobserved determinants of teen employment ε.

**Nuisance models:**
- Primary: Gradient Boosting (n_estimators=150, max_depth=3)
- Robust check: LassoCV
- Cross-fitting: 5-fold (RANDOM_STATE=42)

**Data:** 50 U.S. states × 22 years (2000–2021), N = 1,100 observations.
Confounders W: state GDP growth (%), adult unemployment (%), LFPR (%), 21 year dummies, 3 region dummies.
        """)
    with col_m2:
        st.markdown("""
**Why DML outperforms naive OLS here**

High-MW states (CA, MA, WA) are also economically stronger: +1.1 pp GDP growth, −1.3 pp unemployment vs. low-MW states. This positive confounding pushes OLS toward zero.

DML residualizes both treatment and outcome on W using flexible ML, isolating causal variation in minimum wage orthogonal to economic conditions.

**Threats to identification (summary):**
1. Unobserved time-varying state confounders → bias toward zero; mitigated by border-discontinuity design (Dube et al. 2010)
2. Anticipation effects & reverse causality → ambiguous; event-study leads/lags recommended
3. ATE heterogeneity → CATE estimation via CausalForestDML advised for policy targeting

**Our estimate (−1.28 pp) is likely a lower bound** on the true disemployment effect in absolute value.
        """)

with st.expander("📚 Key References"):
    st.markdown("""
- Chernozhukov et al. (2018). *Double/debiased machine learning for treatment and structural parameters.* **Econometrics Journal**, 21(1), C1–C68.
- Dube, Lester & Reich (2010). *Minimum wage effects across state borders.* **Review of Economics and Statistics**, 92(4), 945–964.
- Neumark & Wascher (1992/2006). *Minimum wages and employment.* Multiple publications.
- Meer & West (2016). *Effects of the minimum wage on employment dynamics.* **Journal of Human Resources**, 51(2), 500–522.
- Angrist & Pischke (2009). *Mostly Harmless Econometrics.* Princeton University Press.
    """)

st.markdown(
    '<div style="text-align:center; font-size:0.75rem; color:#9ab0c8; margin-top:24px; font-family:\'IBM Plex Mono\',monospace;">'
    'ECON 5200 | Causal Machine Learning &amp; Applied Analytics | Spring 2026'
    '</div>',
    unsafe_allow_html=True
)
