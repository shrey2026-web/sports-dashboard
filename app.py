import os
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="NBA Performance Dashboard", layout="wide")

DATA_PATH = "data/games.csv"


@st.cache_data
def load_and_tidy(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        st.error(f"Missing file: {path}. Upload games.csv into the repo at data/games.csv.")
        st.stop()

    if os.path.getsize(path) == 0:
        st.error(f"File is empty: {path}. Re-upload a non-empty CSV.")
        st.stop()

    df = pd.read_csv(path)

    # Create standard date
    if "GAME_DATE_EST" not in df.columns:
        st.error("Expected column GAME_DATE_EST not found. Check that this is the Kaggle NBA games.csv file.")
        st.write("Detected columns:", list(df.columns))
        st.stop()

    df["date"] = pd.to_datetime(df["GAME_DATE_EST"], errors="coerce")

    # Keep only completed games if available
    if "GAME_STATUS_TEXT" in df.columns:
        df = df[df["GAME_STATUS_TEXT"].astype(str).str.lower().eq("final")].copy()

    required = {"HOME_TEAM_ID", "VISITOR_TEAM_ID", "PTS_home", "PTS_away"}
    if not required.issubset(df.columns):
        st.error("Expected home/away score columns not found. Check dataset schema.")
        st.stop()

    # Build tidy team-game rows
    home = pd.DataFrame({
        "date": df["date"],
        "season": df.get("SEASON"),
        "team_id": df["HOME_TEAM_ID"],
        "opponent_id": df["VISITOR_TEAM_ID"],
        "home_away": "Home",
        "points": df["PTS_home"],
        "opp_points": df["PTS_away"],
        "fg_pct": df.get("FG_PCT_home"),
        "fg3_pct": df.get("FG3_PCT_home"),
        "ft_pct": df.get("FT_PCT_home"),
        "win": df.get("HOME_TEAM_WINS"),
    })

    away = pd.DataFrame({
        "date": df["date"],
        "season": df.get("SEASON"),
        "team_id": df["VISITOR_TEAM_ID"],
        "opponent_id": df["HOME_TEAM_ID"],
        "home_away": "Away",
        "points": df["PTS_away"],
        "opp_points": df["PTS_home"],
        "fg_pct": df.get("FG_PCT_away"),
        "fg3_pct": df.get("FG3_PCT_away"),
        "ft_pct": df.get("FT_PCT_away"),
        "win": (1 - df["HOME_TEAM_WINS"]) if "HOME_TEAM_WINS" in df.columns else np.nan,
    })

    tidy = pd.concat([home, away], ignore_index=True)
    tidy = tidy.dropna(subset=["date", "points", "opp_points"])

    tidy["team"] = tidy["team_id"].astype(str)
    tidy["opponent"] = tidy["opponent_id"].astype(str)
    tidy["point_diff"] = tidy["points"] - tidy["opp_points"]
    tidy["month"] = tidy["date"].dt.to_period("M").astype(str)

    return tidy


df = load_and_tidy(DATA_PATH)

# ------------------------------------------------------------
# Analytical objective (explicit requirement)
# ------------------------------------------------------------
st.title("NBA Team Performance Dashboard")
st.markdown(
    "### Analytical Objective\n"
    "This dashboard evaluates how team scoring output relates to shooting efficiency and opponent matchups, "
    "with the goal of identifying sustained performance trends, anomalous games, and matchup-specific strengths or weaknesses."
)

# ------------------------------------------------------------
# Dashboard elements (>=3): dropdowns, date range, slider, metrics
# ------------------------------------------------------------
st.sidebar.header("Controls")

teams = sorted(df["team"].unique())
team = st.sidebar.selectbox("Team (ID)", teams, index=0)

df_t = df[df["team"] == team].copy()

seasons = sorted(df_t["season"].dropna().unique())
season = st.sidebar.selectbox("Season", seasons, index=len(seasons) - 1 if seasons else 0)
df_t = df_t[df_t["season"] == season].copy()

min_d, max_d = df_t["date"].min().date(), df_t["date"].max().date()
start_d, end_d = st.sidebar.date_input(
    "Date range",
    value=(min_d, max_d),
    min_value=min_d,
    max_value=max_d
)
start_d, end_d = pd.to_datetime(start_d), pd.to_datetime(end_d)
df_t = df_t[(df_t["date"] >= start_d) & (df_t["date"] <= end_d)].copy()

rolling = st.sidebar.slider("Rolling window (games)", 1, 15, 5)

# KPI metric cards
k1, k2, k3, k4 = st.columns(4)
k1.metric("Games", int(len(df_t)))
k2.metric("Avg Points", f"{df_t['points'].mean():.1f}")
k3.metric("Avg FG%", f"{df_t['fg_pct'].mean():.3f}" if df_t["fg_pct"].notna().any() else "N/A")
k4.metric("Win %", f"{df_t['win'].mean() * 100:.1f}%" if df_t["win"].notna().any() else "N/A")

# ------------------------------------------------------------
# Tabs (>=2) with distinct purposes
# ------------------------------------------------------------
tab1, tab2 = st.tabs(["Overview & Efficiency", "Matchups & Consistency"])

# ---------------------------
# TAB 1: Overview & Efficiency
# Chart types used here: LINE + SCATTER
# ---------------------------
with tab1:
    st.subheader("Scoring Trend and Efficiency Relationship")

    d = df_t.sort_values("date").copy()
    d["points_roll"] = d["points"].rolling(rolling, min_periods=1).mean()

    # Chart type 1: Line chart
    fig_line = px.line(
        d, x="date", y=["points", "points_roll"],
        title="Points Over Time with Rolling Average"
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # Chart type 2: Scatter plot
    fig_scatter = px.scatter(
        d, x="fg_pct", y="points",
        color="home_away",
        hover_data=["date", "opponent", "point_diff"],
        title="Field Goal Percentage vs Points"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("### Interpretation")
    st.write(
        "The scoring trend provides a season-level view of whether the team’s offensive output is improving, declining, "
        "or remaining stable over time. The rolling average reduces single-game variance and helps distinguish sustained "
        "momentum from isolated spikes. The efficiency scatter suggests how strongly points are tied to shooting performance; "
        "a clearer upward relationship indicates efficiency-driven scoring, while widely scattered outcomes imply that factors "
        "like pace, turnovers, free throws, or overtime are materially influencing total points. Notable outliers represent "
        "games where scoring deviated from what shooting efficiency alone would predict, and those games are candidates for deeper review."
    )

# ---------------------------
# TAB 2: Matchups & Consistency
# Chart types used here: BAR + HEATMAP + HISTOGRAM
# ---------------------------
with tab2:
    st.subheader("Opponent Matchups and Outcome Stability")

    # Chart type 3: Bar chart
    matchup = (df_t.groupby("opponent")["point_diff"]
               .mean()
               .sort_values(ascending=False)
               .reset_index(name="avg_point_diff"))

    fig_bar = px.bar(
        matchup.head(10),
        x="opponent",
        y="avg_point_diff",
        title="Top 10 Opponents by Average Point Differential"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Chart type 4: Heatmap
    pivot = pd.pivot_table(df_t, index="month", columns="opponent", values="points", aggfunc="mean")
    if pivot.shape[1] > 12:
        top_opps = df_t["opponent"].value_counts().head(12).index
        pivot = pivot[top_opps]

    fig_heat = px.imshow(
        pivot,
        aspect="auto",
        title="Average Points Heatmap (Month × Opponent)"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Chart type 5: Histogram (extra, still distinct)
    fig_hist = px.histogram(
        df_t, x="point_diff", nbins=30,
        title="Distribution of Point Differential"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("### Interpretation")
    st.write(
        "The matchup bar chart highlights opponents against whom the team consistently performs well or poorly, measured by average point differential. "
        "Strong positive differentials indicate favorable matchups, while persistent negative differentials may reveal structural weaknesses such as style conflicts "
        "or defensive mismatches. The month-by-opponent heatmap adds temporal context by showing whether performance against specific opponents changes over the season, "
        "which may reflect tactical adjustments, schedule density, fatigue, or roster changes. The point differential distribution summarizes consistency; a tighter distribution "
        "implies stable outcomes, while a wide spread suggests volatility driven by blowout wins or large losses. Together, these visuals support the objective by identifying "
        "where performance is sustainable and where matchup-specific interventions could be most impactful."
    )

st.caption("Data source and update procedure are documented in README.md. Replace data/games.csv with an updated download to refresh the dashboard.")
