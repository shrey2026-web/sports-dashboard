import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="NBA Team Performance Dashboard", layout="wide")

DATA_PATH = "data/games.csv"
# DATA_PATH = "data/processed/games_tidy.csv"

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data(DATA_PATH)

# ---- Objective (put this clearly; required by rubric) ----
st.title("NBA Performance Dashboard")
st.markdown("**Objective:** Analyze team scoring + shooting efficiency trends and identify matchup patterns vs opponents.")

# ---- Sidebar filters (>=3 dashboard elements) ----
st.sidebar.header("Filters")
teams = sorted(df["team"].unique())
team = st.sidebar.selectbox("Team", teams, index=0)

df_t = df[df["team"] == team].copy()

min_d, max_d = df_t["date"].min().date(), df_t["date"].max().date()
d1, d2 = st.sidebar.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
d1, d2 = pd.to_datetime(d1), pd.to_datetime(d2)
df_t = df_t[(df_t["date"] >= d1) & (df_t["date"] <= d2)].copy()

opps = ["All"] + sorted(df_t["opponent"].unique())
opp = st.sidebar.selectbox("Opponent", opps, index=0)
if opp != "All":
    df_t = df_t[df_t["opponent"] == opp].copy()

rolling = st.sidebar.slider("Rolling window (games)", 1, 15, 5)

# ---- KPI cards ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Games", len(df_t))
c2.metric("Avg Points", f"{df_t['points'].mean():.1f}")
c3.metric("Avg FG%", f"{df_t['fg_pct'].mean():.3f}" if "fg_pct" in df_t.columns else "N/A")
c4.metric("Win %", f"{df_t['win'].mean()*100:.1f}%" if "win" in df_t.columns else "N/A")

tab1, tab2 = st.tabs(["Trends", "Matchups & Patterns"])

# -------------------------
# TAB 1: Trends (Line + Scatter)
# -------------------------
with tab1:
    st.subheader("Trend analysis over time")

    ts = df_t.sort_values("date").copy()
    ts["points_roll"] = ts["points"].rolling(rolling, min_periods=1).mean()
    ts["fg_roll"] = ts["fg_pct"].rolling(rolling, min_periods=1).mean() if "fg_pct" in ts.columns else np.nan

    # Line chart (Chart type 1)
    fig_line = px.line(ts, x="date", y=["points", "points_roll"], title="Points and Rolling Average")
    st.plotly_chart(fig_line, use_container_width=True)

    # Scatter (Chart type 2)
    if "fg_pct" in df_t.columns:
        fig_scatter = px.scatter(
            df_t, x="fg_pct", y="points",
            color="home_away",
            hover_data=["date", "opponent", "point_diff"],
            title="Scoring vs Shooting Efficiency (FG%)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("### Interpretation")
    st.write(
        "- The rolling points line highlights the underlying scoring trend, reducing single-game noise.\n"
        "- If points rise while FG% stays flat, scoring may be driven by pace/FTs rather than shooting efficiency.\n"
        "- Outliers (high points but low FG%) can indicate unusual games (many FTs, turnovers forced, etc.)."
    )

# -------------------------
# TAB 2: Matchups (Bar + Heatmap)
# -------------------------
with tab2:
    st.subheader("Opponent matchup patterns")

    # Bar chart (Chart type 3)
    by_opp = (df_t.groupby("opponent")["point_diff"]
              .mean()
              .sort_values(ascending=False)
              .reset_index(name="avg_point_diff"))

    fig_bar = px.bar(by_opp.head(12), x="opponent", y="avg_point_diff",
                     title="Best Matchups (Avg Point Differential) – Top 12")
    st.plotly_chart(fig_bar, use_container_width=True)

    # Heatmap (Chart type 4)
    pivot = pd.pivot_table(
        df_t,
        index="month",
        columns="opponent",
        values="points",
        aggfunc="mean"
    )

    # keep readable
    if pivot.shape[1] > 12:
        top_opps = df_t["opponent"].value_counts().head(12).index
        pivot = pivot[top_opps]

    fig_heat = px.imshow(pivot, aspect="auto", title="Avg Points Heatmap (Month × Opponent)")
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("### Interpretation")
    st.write(
        "- Point differential by opponent shows which matchups are systematically favorable/unfavorable.\n"
        "- The heatmap can reveal time-based shifts (early season vs late season) indicating adjustments or schedule effects.\n"
        "- If an opponent flips from strong to weak (or vice versa) across months, investigate roster changes or back-to-back games."
    )

st.caption("Data: derived from the provided games.csv. Refresh by replacing data/raw/games.csv and rerunning prepare_data.py.")
