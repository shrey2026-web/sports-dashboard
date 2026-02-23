import pandas as pd

RAW_PATH = "data/raw/games.csv"
OUT_PATH = "data/processed/games_tidy.csv"

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

def main():
    df = pd.read_csv(RAW_PATH)

    # Keep only "Final" games (optional but clean)
    if "GAME_STATUS_TEXT" in df.columns:
        df = df[df["GAME_STATUS_TEXT"].astype(str).str.lower().eq("final")].copy()

    # Parse date
    df["date"] = pd.to_datetime(df["GAME_DATE_EST"], errors="coerce")

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

    # AWAY rows (win is inverse of HOME_TEAM_WINS)
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
        "win": (1 - df.get("HOME_TEAM_WINS")) if "HOME_TEAM_WINS" in df.columns else None,
    })

    tidy = pd.concat([home, away], ignore_index=True)

    # Add names
    tidy["team"] = tidy["team_id"].map(TEAM_ID_TO_NAME).fillna(tidy["team_id"].astype(str))
    tidy["opponent"] = tidy["opponent_id"].map(TEAM_ID_TO_NAME).fillna(tidy["opponent_id"].astype(str))

    # Useful derived metrics
    tidy["point_diff"] = tidy["points"] - tidy["opp_points"]
    tidy["month"] = tidy["date"].dt.to_period("M").astype(str)

    # Drop rows with missing core values
    tidy = tidy.dropna(subset=["date", "team", "opponent", "points", "opp_points"])

    tidy.to_csv(OUT_PATH, index=False)
    print(f"Saved tidy dataset → {OUT_PATH} | rows={len(tidy):,}")

if __name__ == "__main__":
    main()
