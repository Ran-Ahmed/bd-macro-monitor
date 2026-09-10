import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Bangladesh Macro-Financial Monitor", layout="wide", page_icon="🇧🇩")

# ---------------- CONFIGURATION ----------------
INDICATORS = {
    "FI.RES.TOTL.DT.US": ("Forex Reserves", "USD Bn", 1e9),
    "FP.CPI.TOTL.ZG":    ("Inflation (CPI)", "%", 1),
    "BX.TRF.PWKR.DT.US": ("Remittance Inflows", "USD Bn", 1e9),
    "NY.GDP.MKTP.KD.ZG": ("GDP Growth", "%", 1),
    "PA.NUS.FCRF":       ("Exchange Rate (BDT/USD)", "BDT", 1),
    "FR.INR.LEND":       ("Bank Lending Rate", "%", 1),
}

@st.cache_data(ttl=86400)
def fetch_series(code):
    url = ("https://api.worldbank.org/v2/country/BGD/indicator/"
           f"{code}?date=2003:2025&format=json&per_page=100")
    payload = requests.get(url, timeout=20).json()
    records = payload[1] if len(payload) > 1 else []
    df = pd.DataFrame([{"Year": int(r["date"]), "Value": r["value"]}
                       for r in records if r["value"] is not None])
    return df.sort_values("Year").reset_index(drop=True)

# ---------------- HEADER ----------------
st.title("🇧 Bangladesh Macro-Financial Monitor")
st.caption("Live macroeconomic intelligence for retail investors & research • "
           "Data: World Bank Open Data API • Built by Md. Raiyan Ahmed, Research Analyst @ Investaloy")

# ---------------- KPI CARDS ----------------
cols = st.columns(3)
for i, (code, (name, unit, div)) in enumerate(INDICATORS.items()):
    df = fetch_series(code)
    latest = df.iloc[-1]
    cols[i % 3].metric(f"{name} ({int(latest['Year'])})",
                       f"{latest['Value']/div:,.1f}" if div > 1 else f"{latest['Value']:,.2f}")

# ---------------- HISTORICAL CHARTS ----------------
st.subheader("Historical Trends (2003 – 2025)")
chart_cols = st.columns(2)
for i, (code, (name, unit, div)) in enumerate(INDICATORS.items()):
    df = fetch_series(code)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Year"], y=df["Value"]/div, mode="lines+markers",
                             line=dict(color="#006a4e", width=2.5), name=name))
    fig.update_layout(title=f"{name} ({unit})", template="plotly_white",
                      height=320, margin=dict(l=20, r=20, t=50, b=20))
    chart_cols[i % 2].plotly_chart(fig, use_container_width=True)

# ---------------- ANALYST COMMENTARY ----------------
st.subheader("📝 Analyst Commentary")
st.info("Quarterly commentary: e.g., 'Declining forex reserves pressure the BDT; "
        "watch import-dependent DSE sectors.' — [Your Name]")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("About the Analyst")
    st.write("**[Your Name]**")
    st.write("BBA (Finance), University of Dhaka")
    st.write("Research Analyst, Investaloy")
    st.write("Millennium Fellow • Aspire Leader")
    st.caption("Data refreshes automatically every 24 hours.")
