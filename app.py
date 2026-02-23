import os
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(page_title="NBA Performance Dashboard", layout="wide")

# --------------------------------------------------
# DATA PATH (must match your repo)
# --------------------------------------------------
DATA_PATH = "data/games.csv"

# --------------------------------------------------
# Load + Clean + Reshape Dataset
# --------------------------------------------------
@st.cache_data
def load_and_tidy(path: str) -> pd.DataFrame:

    if not os.path.exists(path):
        st.error(f"Missing file: {path}")
        st.stop()

    df = pd.read_csv(path)

    # Convert date
    df["date"] = pd.to_datetime(df["GAME_DATE_EST"], errors="coerce")

    # Keep only completed games
    if "GAME_STATUS_TEXT" in df.columns:
        df = df[df["GAME_STATUS_TEXT"].astype(str).str.lower().eq("final")].copy()

    # HOME rows
    home = pd.DataFrame({
        "date": df["date"],
        "season": df["SEASON"],
        "team_id": df["HOME_TEAM_ID"],
        "opponent_id": df["VISITOR_TEAM_ID"],
        "home_away": "Home",
        "points": df["PTS_home"],
        "opp_points": df["PTS_away"],
        "fg_pct": df.get("FG_PCT_home"),
        "win": df.get("HOME_TEAM_WINS"),
    })

    # AWAY rows
    away = pd.DataFrame({
        "date": df["date"],
        "season": df["SEASON"],
        "team_id": df["VISITOR_TEAM_ID"],
        "opponent_id": df["HOME_TEAM_ID"],
        "home_away": "Away",
        "points": df["PTS_away"],
        "opp_points": df["PTS_home"],
        "fg_pct": df.get("FG_PCT_away"),
        "win": (1 - df["HOME_TEAM_WINS"]) if "HOME_TEAM_WINS" in df.columns else np.nan,
    })

    tidy = pd.concat([home, away], ignore_index=True)

    # Use team IDs as team labels (simple & safe)
    tidy["team"] = tidy["team_id"].astype(str)
    tidy["opponent"] = tidy["opponent_id"].astype(str)

    # Derived metrics
    tidy["point_diff"] = tidy["points"] - tidy["opp_points"]
    tidy["month"] = tidy["date"].dt.to_period("M").astype(str)

    tidy = tidy.dropna(subset=["date", "points", "opp_points"])

    return tidy


df = load_and_tidy(DATA_PATH)

# --------------------------------------------------
# Objective (Required in rubric)
# --------------------------------------------------
st.title("NBA Team Performance Dashboard")
st.markdown(
    "**Objective:** Analyze scoring trends, shooting efficiency, and matchup performance across NBA seasons."
)

# --------------------------------------------------
# Sidebar Controls (>=3 dashboard elements)
# --------------------------------------------------
st.sidebar.header("Filters")

teams = sorted(df["team"].unique())
team = st.sidebar.selectbox("Select Team (by ID)", teams)

df_team = df[df["team"] == team].copy()

seasons = sorted(df_team["season"].unique())
season = st.sidebar.selectbox("Season", seasons)

df_team = df_team[df_team["season"] == season]

min_date = df_team["date"].min().date()
max_date = df_team["date"].max().date()

start_date, end_date = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

df_team = df_team[
    (df_team["date"] >= pd.to_datetime(start_date)) &
    (df_team["date"] <= pd.to_datetime(end_date))
]

rolling_window = st.sidebar.slider("Rolling Window (Games)", 1, 15, 5)

# --------------------------------------------------
# KPI Metrics
# --------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Games", len(df_team))
col2.metric("Avg Points", f"{df_team['points'].mean():.1f}")
col3.metric("Avg FG%", f"{df_team['fg_pct'].mean():.3f}" if "fg_pct" in df_team.columns else "N/A")
col4.metric("Win %", f"{df_team['win'].mean()*100:.1f}%" if "win" in df_team.columns else "N/A")

# --------------------------------------------------
# Tabs (Required)
# --------------------------------------------------
tab1, tab2 = st.tabs(["Trends", "Matchups & Patterns"])

# --------------------------------------------------
# TAB 1: Trends (Line + Scatter)
# --------------------------------------------------
with tab1:

    st.subheader("Scoring Trend Over Time")

    df_team = df_team.sort_values("date").copy()
    df_team["rolling_points"] = df_team["points"].rolling(rolling_window, min_periods=1).mean()

    # Line chart
    fig_line = px.line(
        df_team,
        x="date",
        y=["points", "rolling_points"],
        title="Points and Rolling Average"
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # Scatter chart
    fig_scatter = px.scatter(
        df_team,
        x="fg_pct",
        y="points",
        color="home_away",
        hover_data=["date", "opponent", "point_diff"],
        title="Shooting Efficiency vs Points"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("### Interpretation")
    st.write(
        "- The rolling average reveals underlying scoring momentum.\n"
        "- Strong positive correlation between FG% and points indicates efficiency-driven scoring.\n"
        "- Outliers may represent extreme shooting nights or overtime games."
    )

# --------------------------------------------------
# TAB 2: Matchups (Bar + Heatmap)
# --------------------------------------------------
with tab2:

    st.subheader("Opponent Performance")

    # Bar chart
    matchup = (
        df_team.groupby("opponent")["point_diff"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig_bar = px.bar(
        matchup.head(12),
        x="opponent",
        y="point_diff",
        title="Average Point Differential vs Opponents"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Heatmap
    pivot = pd.pivot_table(
        df_team,
        index="month",
        columns="opponent",
        values="points",
        aggfunc="mean"
    )

    if pivot.shape[1] > 12:
        top_opps = df_team["opponent"].value_counts().head(12).index
        pivot = pivot[top_opps]

    fig_heat = px.imshow(
        pivot,
        aspect="auto",
        title="Average Points Heatmap (Month × Opponent)"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("### Interpretation")
    st.write(
        "- Positive point differentials indicate favorable matchups.\n"
        "- Heatmap patterns reveal season progression and opponent-specific scoring variability.\n"
        "- Late-season performance shifts may indicate tactical adjustments or fatigue."
    )

st.caption("Data source: NBA Games Dataset (Kaggle). Replace data/games.csv to refresh.")
