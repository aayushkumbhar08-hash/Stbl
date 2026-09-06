import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Collateral Engine", layout="wide", initial_sidebar_state="expanded")

# --- BULLETPROOF STATE INITIALIZATION ---
defaults = {
    "base_margin": 10000000.0,
    "equities_haircut": 15.0,
    "corp_bonds_haircut": 12.0,
    "ust_haircut": 2.0,
    "cash_haircut": 0.0,
    "is_shock": False,
    "market_crash_active": False
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- PREMIUM UI THEME INJECTION ---
st.markdown("""
<style>
    /* Global Palantir/Stripe Aesthetic */
    .stApp {
        background-color: #F7F5F0;
    }
    
    /* Typography & Colors */
    h1, h2, h3, .stMarkdown, p, div {
        color: #111827;
        font-family: 'Inter', sans-serif;
    }
    
    /* Accent Hero */
    .purple-accent {
        color: #7C3AED;
        font-weight: 800;
    }
    
    /* Dark Terminal Card */
    .dark-terminal {
        background-color: #18181B;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        color: #F3F4F6;
        border: 1px solid #3F3F46;
        margin-top: 2rem;
    }
    
    .terminal-header {
        display: flex;
        gap: 8px;
        margin-bottom: 20px;
    }
    
    .terminal-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }
    .dot-red { background-color: #EF4444; }
    .dot-yellow { background-color: #F59E0B; }
    .dot-green { background-color: #10B981; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0B0F19;
    }
    [data-testid="stSidebar"] * {
        color: #F3F4F6 !important;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        color: #7C3AED !important;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>Optimize your institutional <span class='purple-accent'>collateral</span></h1>", unsafe_allow_html=True)

# --- STRICT SOLVER DATA FORMATTING ---
def run_ctd_optimization(margin_req, haircuts, amounts_owned):
    assets_order = ["Cash", "US Treasuries", "Corporate Bonds", "Equities"]
    post_haircut_values = [0.0, 0.0, 0.0, 0.0]
    total_allocated = 0.0
    remaining_req = margin_req
    
    for i, asset in enumerate(assets_order):
        if remaining_req <= 0:
            continue
            
        nominal_avail = amounts_owned[asset]
        hc = haircuts[asset]
        effective_avail = nominal_avail * (1.0 - hc)
        
        if effective_avail >= remaining_req:
            post_haircut_values[i] = float(remaining_req)
            total_allocated += float(remaining_req)
            remaining_req = 0.0
        else:
            post_haircut_values[i] = float(effective_avail)
            total_allocated += float(effective_avail)
            remaining_req -= effective_avail
            
    return {
        "status": "Optimal" if remaining_req <= 0.001 else "Infeasible",
        "post_haircut_values": post_haircut_values,
        "total_nominal_allocated": total_allocated
    }

# --- DEFAULT ASSUMPTIONS ---
amounts_owned = {
    "Cash": 6_000_000.0,
    "US Treasuries": 10_000_000.0,
    "Corporate Bonds": 6_000_000.0,
    "Equities": 10_000_000.0
}

# --- TOP-TO-BOTTOM REACTIVE EXECUTION (NO CALLBACKS) ---
st.sidebar.markdown("<div style='font-size:0.8rem; letter-spacing:1px; color:#9CA3AF;'>APEX PRIME // RISK DESK</div><br>", unsafe_allow_html=True)

live_margin = st.sidebar.number_input("Base Margin Requirement ($)", value=st.session_state["base_margin"], step=500_000.0)

st.sidebar.subheader("Asset Haircuts (%)")
eq_hc_input = st.sidebar.slider("Equities Haircut", 0.0, 100.0, st.session_state["equities_haircut"])
corp_hc_input = st.sidebar.slider("Corporate Bonds Haircut", 0.0, 100.0, st.session_state["corp_bonds_haircut"])
ust_hc_input = st.sidebar.slider("US Treasuries Haircut", 0.0, 100.0, st.session_state["ust_haircut"])
cash_hc_input = st.sidebar.slider("Cash Haircut", 0.0, 100.0, st.session_state["cash_haircut"])

# Demo Crash Buttons (as exactly requested)
st.sidebar.markdown("---")
if st.sidebar.button("💥 Simulate Severe Market Crash", type="primary", use_container_width=True):
    st.session_state["market_crash_active"] = True
    st.session_state["equities_haircut"] = 60.0  
    st.session_state["corp_bonds_haircut"] = 35.0
    st.session_state["base_margin"] = st.session_state.get("base_margin", 10000000.0) * 1.5 
    st.rerun()

if st.sidebar.button("🔄 Reset to Normal Market", use_container_width=True):
    st.session_state["market_crash_active"] = False
    st.session_state["equities_haircut"] = 15.0
    st.session_state["corp_bonds_haircut"] = 12.0
    st.session_state["base_margin"] = 10000000.0
    st.rerun()

# Sync inputs back to state for the next run
st.session_state["base_margin"] = live_margin
st.session_state["equities_haircut"] = eq_hc_input
st.session_state["corp_bonds_haircut"] = corp_hc_input
st.session_state["ust_haircut"] = ust_hc_input
st.session_state["cash_haircut"] = cash_hc_input

haircuts = {
    "Cash": cash_hc_input / 100.0,
    "US Treasuries": ust_hc_input / 100.0,
    "Corporate Bonds": corp_hc_input / 100.0,
    "Equities": eq_hc_input / 100.0
}

# --- EXECUTE PIPELINE ---
results = run_ctd_optimization(live_margin, haircuts, amounts_owned)

# --- DASHBOARD METRICS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Required Margin", f"${live_margin:,.2f}")
with col2:
    st.metric("Total Pledged", f"${results['total_nominal_allocated']:,.2f}")
with col3:
    if results["status"] == "Optimal":
        st.metric("Buffer Status", "SAFE", delta="Optimal")
    else:
        st.metric("Buffer Status", "BREACHED", delta="-DEFICIT", delta_color="inverse")

# --- SAFE PLOTLY RENDERING IN DARK TERMINAL ---
st.markdown("""
<div class="dark-terminal">
    <div class="terminal-header">
        <div class="terminal-dot dot-red"></div>
        <div class="terminal-dot dot-yellow"></div>
        <div class="terminal-dot dot-green"></div>
        <span style="margin-left: 10px; font-family: monospace; color: #9CA3AF; font-size: 0.85rem;">CTD Shadow Frontier</span>
    </div>
""", unsafe_allow_html=True)

post_vals = results.get("post_haircut_values", [0.0, 0.0, 0.0, 0.0])
if any(v > 0 for v in post_vals):
    chart_data = pd.DataFrame({
        "Asset Class": ["Cash", "US Treasuries", "Corporate Bonds", "Equities"],
        "Pledged Value ($)": post_vals
    })

    fig = px.bar(
        chart_data,
        x="Asset Class",
        y="Pledged Value ($)",
        color="Asset Class",
        color_discrete_sequence=["#34D399", "#9333EA", "#FBBF24", "#7C3AED"]
    )
    
    fig.add_hline(y=live_margin, line_dash="dash", line_color="#EF4444", annotation_text="REQUIRED MARGIN", annotation_font_color="#EF4444")
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#111827", family="sans-serif", size=14),
        xaxis=dict(
            title_font=dict(color="#111827", size=14),
            tickfont=dict(color="#374151", size=12),
            showgrid=False
        ),
        yaxis=dict(
            title_font=dict(color="#111827", size=14),
            tickfont=dict(color="#374151", size=12),
            showgrid=True,
            gridcolor="#D1D5DB"
        ),
        margin=dict(t=40, b=40, l=40, r=40),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Solver Infeasible: Adjust caps or margin thresholds.")

st.markdown("</div>", unsafe_allow_html=True)
