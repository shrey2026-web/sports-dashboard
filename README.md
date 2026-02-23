# NBA Team Performance Dashboard (Streamlit)

## 1. Project Objective

The objective of this dashboard is to analyze NBA team performance using historical game data. The dashboard explores scoring trends, shooting efficiency, matchup strengths, and performance consistency across seasons. It provides interactive filters that allow users to examine trends over time, evaluate opponent matchups, and assess statistical relationships between efficiency and scoring output.

---

## 2. Data Source (Provenance)

The dataset used in this project is the NBA Games dataset obtained from Kaggle:

Source:
https://www.kaggle.com/datasets/nathanlauga/nba-games

The dataset contains historical NBA game-level data including:

- Game date
- Season
- Home and away team IDs
- Points scored (home and away)
- Field goal percentages
- Win/loss indicators
- Additional box score statistics

The dataset is publicly available and does not require special credentials beyond a free Kaggle account.

---

## 3. Data Collection Methodology

The dataset was downloaded directly from Kaggle in CSV format.

Steps followed:

1. Access the Kaggle NBA Games dataset page.
2. Download the compressed dataset.
3. Extract the file `games.csv`.
4. Upload `games.csv` into the project repository under the `data/` directory.
5. The Streamlit application reshapes the raw dataset into a tidy team-level format at runtime:
   - Converts home and away records into individual team-game rows.
   - Computes derived metrics such as point differential.
   - Extracts month from the game date.
   - Filters completed games.

No scraping or API calls are performed during app execution. All transformations occur locally within the application.

---

## 4. Data Processing and Transformation

The raw dataset contains separate columns for home and away teams. During application startup, the following transformations are applied:

- Convert `GAME_DATE_EST` to datetime format.
- Filter for completed games only.
- Create one row per team per game.
- Compute:
  - `point_diff = points - opponent_points`
  - `month` extracted from game date
- Retain relevant columns for visualization.

This processing ensures compatibility with interactive filtering and visualization.

---

## 5. Dashboard Features

The deployed Streamlit dashboard includes:

- Interactive team selection
- Season filter
- Date range filter
- Rolling average slider
- KPI metrics (games played, average points, FG%, win rate)
- Five visualizations:
  1. Line chart (scoring trend with rolling average)
  2. Scatter plot (FG% vs points)
  3. Bar chart (average point differential by opponent)
  4. Heatmap (monthly scoring vs opponent)
  5. Histogram (distribution of point differential)

Each visualization includes interpretive analysis describing observed trends and patterns.

---

## 6. Update Procedure (Sustainability)

To refresh the dashboard with updated data:

1. Download the latest version of the NBA Games dataset from Kaggle.
2. Replace the existing `data/games.csv` file in the repository.
3. Commit and push the updated file to GitHub.
4. Streamlit Community Cloud will automatically redeploy the app.

No code modifications are required unless the dataset schema changes.

---

## 7. Deployment

The application is deployed on Streamlit Community Cloud.

Public URL:
https://sports-dashboard.streamlit.app/

GitHub Repository:
https://github.com/shrey2026-web/sports-dashboard/
