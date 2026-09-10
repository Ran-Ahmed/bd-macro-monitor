import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Bangladesh Macro-Financial Monitor", layout="wide", page_icon="🇧🇩")

# ---------------- CONFIGURATION (live-verified World Bank codes) ----------------
INDICATORS = {
    "FP.CPI.TOTL.ZG":       ("Inflation (CPI)", "%"),
    "NY.GDP.MKTP.KD.ZG":    ("GDP Growth", "%"),
    "PA.NUS.FCRF":          ("Exchange Rate", "BDT/USD"),
    "FR.INR.LEND":          ("Bank Lending Rate", "%"),
    "BX.TRF.PWKR.DT.GD.ZS": ("Remittances Received", "% of GDP"),
    "BN.CAB.XOKA.GD.ZS":    ("Current Account Balance", "% of GDP"),
}

@st.cache_data(ttl=86400)
def fetch_series(code):
    """Fetch one indicator from the World Bank API. Defensive: never crashes."""
    url = ("https://api.worldbank.org/v2/country/BGD/indicator/"
           f"{code}?date=2000:2026&format=json&per_page=100")
    try:
        payload = requests.get(url, timeout=20).json()
    except Exception:
        return pd.DataFrame(columns=["Year", "Value"])
    records = []
    if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], list):
        records = payload[1]
    rows = [{"Year": int(r["date"]), "Value": float(r["value"])}
            for r in records if r.get("value") is not None]
    df = pd.DataFrame(rows, columns=["Year", "Value"])
    return df.sort_values("Year").reset_index(drop=True)

# ---------------- LOAD ALL DATA SAFELY ----------------
data, missing = {}, []
for code, (name, unit) in INDICATORS.items():
    df = fetch_series(code)
    if df.empty:
        missing.append(name)
    else:
        data[code] = df

# ---------------- HEADER ----------------
st.title("🇧🇩 Bangladesh Macro-Financial Monitor")
st.caption("Live macroeconomic intelligence for retail investors & research • "
           "Data: World Bank Open Data API • Built by Md. Raiyan Ahmed, Research Analyst @ Investaloy")

if missing:
    st.warning("⚠️ Data temporarily unavailable for: " + ", ".join(missing))
if not data:
    st.error("Could not reach the World Bank API. Click ⋮ (top-right) → Rerun.")
    st.stop()

# ---------------- KPI CARDS ----------------
cols = st.columns(3)
for i, (code, df) in enumerate(data.items()):
    name, unit = INDICATORS[code]
    latest = df.iloc[-1]
    cols[i % 3].metric(label=f"{name} — {unit} ({int(latest['Year'])})",
                       value=f"{latest['Value']:,.2f}")

# ---------------- HISTORICAL CHARTS ----------------
st.subheader("Historical Trends (2000 – 2025)")
chart_cols = st.columns(2)
for i, (code, df) in enumerate(data.items()):
    name, unit = INDICATORS[code]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Year"], y=df["Value"], mode="lines+markers",
                             line=dict(color="#006a4e", width=2.5), name=name))
    fig.update_layout(title=f"{name} ({unit})", template="plotly_white",
                      height=320, margin=dict(l=20, r=20, t=50, b=20))
    chart_cols[i % 2].plotly_chart(fig, use_container_width=True)

# ---------------- ANALYST COMMENTARY ----------------
st.subheader("📝 Analyst Commentary")
st.info("Quarterly commentary by Md. Raiyan Ahmed: 'Remittances at ~7.4% of GDP remain the key "
        "support for the BDT. Watch the inflation–lending rate spread and the current account "
        "for implications on DSE bank valuations.'")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("About the Analyst")
    st.write("**Md. Raiyan Ahmed**")
    st.write("BBA (Finance), University of Dhaka")
    st.write("Research Analyst, Investaloy")
    st.write("Millennium Fellow • Aspire Leader")
    st.divider()
    st.subheader("Data Status")
    for code, df in data.items():
        name, unit = INDICATORS[code]
        st.caption(f"• {name}: latest {int(df.iloc[-1]['Year'])}")
    st.caption("Auto-refreshes every 24 hours.")
