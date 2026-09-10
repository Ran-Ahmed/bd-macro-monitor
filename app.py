import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Bangladesh Macro-Financial Monitor", layout="wide", page_icon="🇧")

# ---------------- CONFIGURATION ----------------
INDICATORS = {
    "FP.CPI.TOTL.ZG":       ("Inflation (CPI)", "%"),
    "NY.GDP.MKTP.KD.ZG":    ("GDP Growth", "%"),
    "PA.NUS.FCRF":          ("Exchange Rate", "BDT/USD"),
    "FR.INR.LEND":          ("Bank Lending Rate", "%"),
    "BX.TRF.PWKR.DT.GD.ZS": ("Remittances Received", "% of GDP"),
    "BN.CAB.XOKA.GD.ZS":    ("Current Account Balance", "% of GDP"),
}

COLOR = {"Undervalued": "#006a4e", "Fair": "#f2a516", "Overvalued": "#f42a41"}

SAMPLE_WATCHLIST = pd.DataFrame({
    "Bank": ["BRAC Bank", "City Bank", "Dutch-Bangla Bank", "Eastern Bank", "Islami Bank BD", "Pubali Bank"],
    "Price (BDT)": [58.4, 24.1, 72.5, 38.2, 45.6, 33.9],
    "P/E Ratio": [7.8, 5.2, 6.1, 5.9, 8.4, 6.6],
    "Dividend Yield (%)": [3.4, 5.1, 4.2, 4.8, 2.9, 3.7],
    "Analyst View": ["Undervalued", "Undervalued", "Fair", "Undervalued", "Fair", "Fair"],
})

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

# ---------------- LOAD MACRO DATA ----------------
data, missing = {}, []
for code, (name, unit) in INDICATORS.items():
    df = fetch_series(code)
    if df.empty:
        missing.append(name)
    else:
        data[code] = df

# ---------------- HEADER ----------------
st.title("🇧 Bangladesh Macro-Financial Monitor")
st.caption("Live macroeconomic intelligence for retail investors & research • "
           "Data: World Bank Open Data API • Built by Md. Raiyan Ahmed, Research Analyst @ Investaloy")

tab_macro, tab_dse, tab_research = st.tabs(["🌍 Macro Monitor", "🏦 DSE Bank Watchlist", "📚 Research & Profile"])

# ================= TAB 1: MACRO =================
with tab_macro:
    if missing:
        st.warning("⚠️ Data temporarily unavailable for: " + ", ".join(missing))
    if not data:
        st.error("Could not reach the World Bank API. Click ⋮ (top-right) → Rerun.")
        st.stop()

    cols = st.columns(3)
    for i, (code, df) in enumerate(data.items()):
        name, unit = INDICATORS[code]
        latest = df.iloc[-1]
        cols[i % 3].metric(label=f"{name} — {unit} ({int(latest['Year'])})",
                           value=f"{latest['Value']:,.2f}")

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

    st.subheader("📝 Analyst Commentary")
    st.info("Quarterly commentary by Md. Raiyan Ahmed: 'Remittances at ~7.4% of GDP remain the key "
            "support for the BDT. Watch the inflation–lending rate spread and the current account "
            "for implications on DSE bank valuations.'")

# ================= TAB 2: DSE WATCHLIST =================
with tab_dse:
    st.subheader("DSE Bank Watchlist")
    st.caption("Compare valuation metrics of listed banks. Upload your own research CSV, or use the template.")

    csv_bytes = SAMPLE_WATCHLIST.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV template", data=csv_bytes,
                       file_name="dse_watchlist_template.csv", mime="text/csv")

    uploaded = st.file_uploader("Upload your watchlist CSV", type=["csv"])
    df_watch = SAMPLE_WATCHLIST
    if uploaded is not None:
        try:
            df_try = pd.read_csv(uploaded)
            required = {"Bank", "Price (BDT)", "P/E Ratio", "Dividend Yield (%)", "Analyst View"}
            if required.issubset(df_try.columns):
                df_watch = df_try
            else:
                st.error("CSV is missing required columns. Showing sample data instead.")
        except Exception:
            st.error("Could not read that CSV. Showing sample data instead.")
    else:
        st.caption("⚠️ Showing SAMPLE data for layout demo. Prices are placeholders, not investment advice.")

    t1, t2 = st.columns(2)
    with t1:
        fig_pe = go.Figure(go.Bar(
            x=df_watch["Bank"], y=df_watch["P/E Ratio"],
            marker_color=[COLOR.get(v, "#888888") for v in df_watch["Analyst View"]]))
        fig_pe.update_layout(title="P/E Ratio by Bank", template="plotly_white", height=360)
        st.plotly_chart(fig_pe, use_container_width=True)
    with t2:
        fig_dy = go.Figure(go.Bar(
            x=df_watch["Bank"], y=df_watch["Dividend Yield (%)"],
            marker_color=[COLOR.get(v, "#888888") for v in df_watch["Analyst View"]]))
        fig_dy.update_layout(title="Dividend Yield (%) by Bank", template="plotly_white", height=360)
        st.plotly_chart(fig_dy, use_container_width=True)

    st.dataframe(df_watch, use_container_width=True, hide_index=True)

# ================= TAB 3: RESEARCH & PROFILE =================
with tab_research:
    st.subheader("About the Analyst")
    st.write("**Md. Raiyan Ahmed** — BBA (Finance), University of Dhaka | Research Analyst @ Investaloy | "
             "Millennium Fellow | Aspire Leader")
    st.write("This dashboard supports my equity research and retail-investor education work. "
             "Below are my professional profiles and published research.")

    c1, c2 = st.columns(2)
    c1.link_button("🔗 LinkedIn", "https://www.linkedin.com/in/md-raiyan-ahmed")
    c2.link_button("🐙 GitHub", "https://github.com/Ran-Ahmed")
    c3, c4 = st.columns(2)
    c3.link_button("📈 Investaloy", "https://www.investaloy.com/")
    c4.link_button("🌐 Millennium Fellowship", "https://www.millenniumfellows.org/")

    st.subheader("📄 Published Research")
    st.info("Coming soon: 'Valuation Analysis of Bangladeshi Listed Banks' — equity research note by Md. Raiyan Ahmed.")

# ---------------- SIDEBAR & FOOTER ----------------
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

st.divider()
st.caption("© 2026 Md. Raiyan Ahmed • Data: World Bank Open Data API • Built with Python, Streamlit & Plotly")
