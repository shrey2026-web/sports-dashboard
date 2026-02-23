import os
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="NBA Dashboard", layout="wide")
DATA_PATH = "data/games.csv"

@st.cache_data
def load_and_tidy(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        st.error(f"Missing file: {path}")
        st.stop()

    df = pd.read_csv(path)

    # date
    df["date"] = pd.to_datetime(df["GAME_DATE_EST"], errors="coerce")

    # optional: only finals
    if "GAME_STATUS_TEXT" in df.columns:
        df = df[df["GAME_STATUS_TEXT"].astype(str).str.lower().eq("final")].copy()

    # home rows
    home = pd.DataFrame({
        "date": df["date"],
        "season": df.get("SEASON"),
        "team_id": df["HOME_TEAM_ID"],
        "opponent_id": df["VISITOR_TEAM_ID"],
        "home_away": "Home",
        "points": df["PTS_home"],
        "opp_points": df["PTS_away"],
        "fg_pct": df.get("FG_PCT_home"),
        "win": df.get("HOME_TEAM_WINS"),
    })

    # away rows
    away = pd.DataFrame({
        "date": df["date"],
        "season": df.get("SEASON"),
        "team_id": df["VISITOR_TEAM_ID"],
        "opponent_id": df["HOME_TEAM_ID"],
        "home_away": "Away",
        "points": df["PTS_away"],
        "opp_points": df["PTS_home"],
        "fg_pct": df.get("FG_PCT_away"),
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

# ---- Objective (rubric) ----
st.title("NBA Team Performance Dashboard")
st.markdown("**Objective:** Explore scoring trends, shooting efficiency, matchup strength, and consistency for an NBA team.")

# ---- Sidebar filters (>=3 elements) ----
st.sidebar.header("Filters")
teams = sorted(df["team"].unique())
team = st.sidebar.selectbox("Team (ID)", teams, index=0)

df_t = df[df["team"] == team].copy()

seasons = sorted(df_t["season"].dropna().unique())
season = st.sidebar.selectbox("Season", seasons, index=len(seasons)-1 if seasons else 0)
df_t = df_t[df_t["season"] == season].copy()

min_d, max_d = df_t["date"].min().date(), df_t["date"].max().date()
start_d, end_d = st.sidebar.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
start_d, end_d = pd.to_datetime(start_d), pd.to_datetime(end_d)
df_t = df_t[(df_t["date"] >= start_d) & (df_t["date"] <= end_d)].copy()

rolling = st.sidebar.slider("Rolling window (games)", 1, 15, 5)

# ---- KPIs ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Games", len(df_t))
c2.metric("Avg Points", f"{df_t['points'].mean():.1f}")
c3.metric("Avg FG%", f"{df_t['fg_pct'].mean():.3f}" if df_t["fg_pct"].notna().any() else "N/A")
c4.metric("Win %", f"{df_t['win'].mean()*100:.1f}%" if df_t["win"].notna().any() else "N/A")

tab1, tab2 = st.tabs(["Trends & Efficiency", "Matchups & Consistency"])

with tab1:
    st.subheader("1) Scoring trend (Line)")
    ts = df_t.sort_values("date").copy()
    ts["points_roll"] = ts["points"].rolling(rolling, min_periods=1).mean()
    fig1 = px.line(ts, x="date", y=["points", "points_roll"], title="Points and Rolling Average")
    st.plotly_chart(fig1, use_container_width=True)
    st.write("**Analysis:** Rolling averages smooth game-to-game variance and highlight sustained scoring streaks or slumps.")

    st.subheader("2) Efficiency vs scoring (Scatter)")
    fig2 = px.scatter(
        df_t, x="fg_pct", y="points",
        color="home_away",
        hover_data=["date", "opponent", "point_diff"],
        title="FG% vs Points (Home/Away)"
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.write("**Analysis:** A positive slope suggests efficiency-driven scoring; outliers indicate unusual games (pace, free throws, OT).")

with tab2:
    st.subheader("3) Matchup strength (Bar)")
    matchup = (df_t.groupby("opponent")["point_diff"].mean()
               .sort_values(ascending=False).reset_index(name="avg_point_diff"))
    fig3 = px.bar(matchup.head(10), x="opponent", y="avg_point_diff", title="Top 10 Opponents by Avg Point Differential")
    st.plotly_chart(fig3, use_container_width=True)
    st.write("**Analysis:** Positive average point differential indicates favorable matchups; persistent negatives show problem opponents.")

    st.subheader("4) Seasonal pattern by opponent (Heatmap)")
    pivot = pd.pivot_table(df_t, index="month", columns="opponent", values="points", aggfunc="mean")
    if pivot.shape[1] > 12:
        top_opps = df_t["opponent"].value_counts().head(12).index
        pivot = pivot[top_opps]
    fig4 = px.imshow(pivot, aspect="auto", title="Avg Points Heatmap (Month × Opponent)")
    st.plotly_chart(fig4, use_container_width=True)
    st.write("**Analysis:** Heatmaps reveal opponent-specific scoring patterns and whether performance shifts across the season timeline.")

    st.subheader("5) Consistency (Histogram)")
    fig5 = px.histogram(df_t, x="point_diff", nbins=30, title="Distribution of Point Differential")
    st.plotly_chart(fig5, use_container_width=True)
    st.write("**Analysis:** A tighter distribution means consistent outcomes; heavy tails indicate volatility (blowouts or collapses).")

st.caption("Data: games.csv (NBA). Upload/replace data/games.csv to refresh.")
