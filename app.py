import os
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------
# Page config
# ------------------------------------------------------------
st.set_page_config(page_title="NBA Performance Dashboard", layout="wide")

# ------------------------------------------------------------
# Data path (must match your repo)
# ------------------------------------------------------------
DATA_PATH = "data/games.csv"

# ------------------------------------------------------------
# Team ID -> Team Name mapping (fixes ugly "1.6106B" labels)
# ------------------------------------------------------------
TEAM_ID_TO_NAME = {
    1610612737: "Atlanta Hawks",
    1610612738: "Boston Celtics",
    1610612739: "Cleveland Cavaliers",
    1610612740: "New Orleans Pelicans",
    1610612741: "Chicago Bulls",
    1610612742: "Dallas Mavericks",
    1610612743: "Denver Nuggets",
    1610612744: "Golden State Warriors",
    1610612745: "Houston Rockets",
    1610612746: "LA Clippers",
    1610612747: "Los Angeles Lakers",
    1610612748: "Miami Heat",
    1610612749: "Milwaukee Bucks",
    1610612750: "Minnesota Timberwolves",
    1610612751: "Brooklyn Nets",
    1610612752: "New York Knicks",
    1610612753: "Orlando Magic",
    1610612754: "Indiana Pacers",
    1610612755: "Philadelphia 76ers",
    1610612756: "Phoenix Suns",
    1610612757: "Portland Trail Blazers",
    1610612758: "Sacramento Kings",
    1610612759: "San Antonio Spurs",
    1610612760: "Oklahoma City Thunder",
    1610612761: "Toronto Raptors",
    1610612762: "Utah Jazz",
    1610612763: "Memphis Grizzlies",
    1610612764: "Washington Wizards",
    1610612765: "Detroit Pistons",
    1610612766: "Charlotte Hornets",
}

# ------------------------------------------------------------
# Load + reshape (Kaggle NBA games.csv)
# ------------------------------------------------------------
@st.cache_data
def load_and_tidy(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        st.error(f"Missing file: {path}. Upload games.csv into the repo at data/games.csv.")
        st.stop()

    if os.path.getsize(path) == 0:
        st.error(f"File is empty: {path}. Re-upload a non-empty CSV.")
        st.stop()

    df = pd.read_csv(path)

    # Validate expected column
    if "GAME_DATE_EST" not in df.columns:
        st.error("Expected column GAME_DATE_EST not found. Make sure you uploaded the Kaggle nba-games games.csv.")
        st.write("Detected columns:", list(df.columns))
        st.stop()

    # Parse date
    df["date"] = pd.to_datetime(df["GAME_DATE_EST"], errors="coerce")

    # Keep only completed games if column exists
    if "GAME_STATUS_TEXT" in df.columns:
        df = df[df["GAME_STATUS_TEXT"].astype(str).str.lower().eq("final")].copy()

    needed = {"HOME_TEAM_ID", "VISITOR_TEAM_ID", "PTS_home", "PTS_away"}
    if not needed.issubset(df.columns):
        st.error("Expected home/away columns not found. Dataset schema does not match.")
        st.stop()

    # HOME rows
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
        "ast": df.get("AST_home"),
        "reb": df.get("REB_home"),
        "win": df.get("HOME_TEAM_WINS"),
    })

    # AWAY rows
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
        "ast": df.get("AST_away"),
        "reb": df.get("REB_away"),
        "win": (1 - df["HOME_TEAM_WINS"]) if "HOME_TEAM_WINS" in df.columns else np.nan,
    })

    tidy = pd.concat([home, away], ignore_index=True)
    tidy = tidy.dropna(subset=["date", "points", "opp_points"])

    # Map IDs to names (THIS fixes your ugly x-axis labels)
    tidy["team"] = tidy["team_id"].map(TEAM_ID_TO_NAME).fillna(tidy["team_id"].astype(str))
    tidy["opponent"] = tidy["opponent_id"].map(TEAM_ID_TO_NAME).fillna(tidy["opponent_id"].astype(str))

    # Derived metrics
    tidy["point_diff"] = tidy["points"] - tidy["opp_points"]
    tidy["month"] = tidy["date"].dt.to_period("M").astype(str)

    return tidy


df = load_and_tidy(DATA_PATH)

# ------------------------------------------------------------
# Objective (rubric requirement)
# ------------------------------------------------------------
st.title("NBA Team Performance Dashboard")
st.markdown(
    "### Analytical Objective\n"
    "This dashboard evaluates how team scoring output relates to shooting efficiency and opponent matchups, "
    "with the goal of identifying sustained performance trends, anomalous games, and matchup-specific strengths or weaknesses."
)

# ------------------------------------------------------------
# Sidebar controls (>=3 dashboard elements)
# ------------------------------------------------------------
st.sidebar.header("Controls")

teams = sorted(df["team"].unique())
team = st.sidebar.selectbox("Team", teams, index=0)

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

# ------------------------------------------------------------
# KPI metric cards
# ------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Games", int(len(df_t)))
k2.metric("Avg Points", f"{df_t['points'].mean():.1f}")
k3.metric("Avg FG%", f"{df_t['fg_pct'].mean():.3f}" if df_t["fg_pct"].notna().any() else "N/A")
k4.metric("Win %", f"{df_t['win'].mean() * 100:.1f}%" if df_t["win"].notna().any() else "N/A")

# ------------------------------------------------------------
# Tabs (>=2) with distinct purpose
# ------------------------------------------------------------
tab1, tab2 = st.tabs(["Overview & Efficiency", "Matchups & Consistency"])

# ------------------------------------------------------------
# TAB 1: Line + Scatter
# ------------------------------------------------------------
with tab1:
    st.subheader("Scoring Trend and Efficiency Relationship")

    d = df_t.sort_values("date").copy()
    d["points_roll"] = d["points"].rolling(rolling, min_periods=1).mean()

    fig_line = px.line(
        d, x="date", y=["points", "points_roll"],
        title="Points Over Time with Rolling Average"
    )
    st.plotly_chart(fig_line, use_container_width=True)

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

# ------------------------------------------------------------
# TAB 2: Bar + Heatmap + Histogram
# ------------------------------------------------------------
with tab2:
    st.subheader("Opponent Matchups and Outcome Stability")

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
    fig_bar.update_xaxes(type="category", tickangle=-35)
    st.plotly_chart(fig_bar, use_container_width=True)

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

# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------
st.caption(
    "Data source and update procedure are documented in README.md. "
)
