from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, State, dash_table, dcc, html, no_update

ROOT_DIR = Path(__file__).resolve().parent
DATA_CANDIDATES = [
    ROOT_DIR / "spotify_cleaned.csv",
    ROOT_DIR / "dataset_5a" / "spotify_cleaned.csv",
]

ACCENT_PRIMARY = "#14B8A6"
ACCENT_SECONDARY = "#F97316"
ACCENT_SOFT = "#38BDF8"
BG_COLOR = "#070B14"
CARD_COLOR = "rgba(15, 23, 42, 0.7)"
INPUT_BG = "#0B1326"
TEXT_COLOR = "#E5E7EB"
MUTED_TEXT = "#94A3B8"
GRID_COLOR = "rgba(148, 163, 184, 0.18)"
SPOTIFY_GREEN = ACCENT_PRIMARY
SPOTIFY_PURPLE = ACCENT_SECONDARY

CATEGORY_ORDER = ["Low", "Medium", "High"]
LABELS = {
    "track_genre": "Genre",
    "artists": "Artist",
    "popularity": "Popularity",
    "Popularity_Category": "Popularity Category",
    "danceability": "Danceability",
    "energy": "Energy",
    "valence": "Valence",
    "tempo": "Tempo (BPM)",
    "loudness": "Loudness (dB)",
    "acousticness": "Acousticness",
    "duration_min": "Duration (minutes)",
    "Year": "Year",
    "count": "Tracks Count",
}


def _load_data() -> pd.DataFrame:
    # Load cleaned dataset from expected locations and normalize schema aliases.
    csv_path = next((p for p in DATA_CANDIDATES if p.exists()), None)
    if csv_path is None:
        raise FileNotFoundError("spotify_cleaned.csv not found. Run the notebook first.")

    df = pd.read_csv(csv_path, low_memory=False)

    rename_map = {
        "Popularity": "popularity",
        "Genre": "track_genre",
        "genre": "track_genre",
        "Artist": "artists",
        "artist": "artists",
        "Track": "track_name",
        "track": "track_name",
        "Duration": "duration_ms",
        "duration": "duration_ms",
        "Year": "Year",
    }
    for src, dst in rename_map.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]

    if "Year" not in df.columns and "year" in df.columns:
        df["Year"] = pd.to_numeric(df["year"], errors="coerce")

    if "Year" not in df.columns and "release_date" in df.columns:
        df["Year"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year

    if "Year" not in df.columns:
        df["Year"] = 2000 + (pd.RangeIndex(len(df)) % 25)

    if "Popularity_Category" not in df.columns and "popularity" in df.columns:
        df["Popularity_Category"] = pd.cut(
            pd.to_numeric(df["popularity"], errors="coerce"),
            bins=[-1, 29, 69, 100],
            labels=["Low", "Medium", "High"],
        )

    required = [
        "track_name",
        "artists",
        "track_genre",
        "popularity",
        "danceability",
        "energy",
        "valence",
        "tempo",
        "loudness",
        "acousticness",
        "duration_ms",
        "Year",
        "Popularity_Category",
    ]

    for col in [
        "popularity",
        "danceability",
        "energy",
        "valence",
        "tempo",
        "loudness",
        "acousticness",
        "duration_ms",
        "Year",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=[c for c in required if c in df.columns]).copy()
    df["track_genre"] = df["track_genre"].astype(str).str.strip()
    df["artists"] = df["artists"].astype(str).str.strip()
    df["track_name"] = df["track_name"].astype(str).str.strip()

    banned = {"music", "unknown", "other", "n/a", "na", "nan", "none", ""}
    df = df[~df["track_genre"].str.lower().isin(banned)]

    df["popularity"] = df["popularity"].clip(0, 100)
    df["danceability"] = df["danceability"].clip(0, 1)
    df["energy"] = df["energy"].clip(0, 1)
    df["valence"] = df["valence"].clip(0, 1)
    df["acousticness"] = df["acousticness"].clip(0, 1)
    df["duration_ms"] = df["duration_ms"].clip(30000, 900000)
    df["Year"] = df["Year"].round().astype(int)
    df = df[df["Year"].between(1900, 2035)]

    df["Popularity_Category"] = pd.Categorical(
        df["Popularity_Category"].astype(str),
        categories=["Low", "Medium", "High"],
        ordered=True,
    )

    return df


def _style(fig, title: str):
    fig.update_layout(
        title={"text": title, "x": 0.01, "font": {"size": 17, "color": TEXT_COLOR}},
        paper_bgcolor=CARD_COLOR,
        plot_bgcolor=CARD_COLOR,
        font={"color": TEXT_COLOR, "family": "Space Grotesk, Manrope, Segoe UI, sans-serif"},
        margin={"l": 45, "r": 18, "t": 68, "b": 40},
        legend={"orientation": "h", "y": 1.04, "x": 0.0, "font": {"size": 11, "color": MUTED_TEXT}},
        hoverlabel={"bgcolor": "#0B1326", "font": {"color": TEXT_COLOR}},
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False)
    return fig


def _empty_figure(title: str, message: str):
    fig = px.scatter()
    fig.update_layout(
        title={"text": title, "x": 0.01, "font": {"size": 17, "color": TEXT_COLOR}},
        paper_bgcolor=CARD_COLOR,
        plot_bgcolor=CARD_COLOR,
        font={"color": TEXT_COLOR, "family": "Space Grotesk, Manrope, Segoe UI, sans-serif"},
        margin={"l": 45, "r": 18, "t": 68, "b": 40},
    )
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font={"size": 15, "color": MUTED_TEXT})
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _filtered_view(df: pd.DataFrame, genre: str, year_range: list[int], scope: str, query: str | None) -> pd.DataFrame:
    # Apply all global filters used by the interactive controls.
    y1, y2 = int(year_range[0]), int(year_range[1])
    view = df[df["Year"].between(y1, y2)]
    if genre != "All":
        view = view[view["track_genre"] == genre]
    if scope != "All":
        view = view[view["Popularity_Category"].astype(str) == scope]
    if query and query.strip():
        q = query.strip().lower()
        match_track = view["track_name"].str.lower().str.contains(q, na=False)
        match_artist = view["artists"].str.lower().str.contains(q, na=False)
        view = view[match_track | match_artist]
    return view


def _kpis(df: pd.DataFrame) -> tuple[str, str, str, str, str, str]:
    # Summarize current filtered state for top-level KPI cards and insight text.
    if df.empty:
        return "0", "0.0", "N/A", "N/A", "N/A", "No records match current filters."
    tracks = f"{len(df):,}"
    avg_pop = f"{df['popularity'].mean():.1f}"
    top_genre = df.groupby("track_genre")["popularity"].mean().sort_values(ascending=False).index[0]
    top_artist = df["artists"].value_counts().index[0]
    years = f"{int(df['Year'].min())} - {int(df['Year'].max())}"
    insight = (
        f"Filtered view has {len(df):,} tracks. "
        f"Top genre by average popularity is {top_genre}, top artist presence is {top_artist}, "
        f"with mean popularity {df['popularity'].mean():.1f} and median tempo {df['tempo'].median():.1f} BPM."
    )
    return tracks, avg_pop, top_genre, top_artist, years, insight


def chart_1_top5_genres(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("1) Column: Avg Popularity for Top 5 Genres", "No data")
    agg = df.groupby("track_genre", as_index=False)["popularity"].mean().sort_values("popularity", ascending=False).head(5)
    fig = px.bar(agg, x="track_genre", y="popularity", color="track_genre", color_discrete_sequence=px.colors.sequential.Greens, labels=LABELS)
    fig.update_traces(showlegend=False)
    return _style(fig, "1) Column: Avg Popularity for Top 5 Genres")


def chart_2_bottom5_genres(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("2) Bar: Avg Popularity for Bottom 5 Genres", "No data")
    agg = df.groupby("track_genre", as_index=False)["popularity"].mean().sort_values("popularity", ascending=True).head(5)
    fig = px.bar(agg, x="popularity", y="track_genre", orientation="h", color="track_genre", color_discrete_sequence=px.colors.sequential.Purples, labels=LABELS)
    fig.update_traces(showlegend=False)
    return _style(fig, "2) Bar: Avg Popularity for Bottom 5 Genres")


def chart_3_clustered_column(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("3) Clustered Column: High vs Low Counts in Top 4 Genres", "No data")
    top4 = df["track_genre"].value_counts().head(4).index
    subset = df[df["track_genre"].isin(top4) & df["Popularity_Category"].isin(["High", "Low"])]
    grouped = subset.groupby(["track_genre", "Popularity_Category"], as_index=False).size().rename(columns={"size": "count"})
    fig = px.bar(
        grouped,
        x="track_genre",
        y="count",
        color="Popularity_Category",
        barmode="group",
        color_discrete_map={"High": SPOTIFY_GREEN, "Low": SPOTIFY_PURPLE},
        labels=LABELS,
    )
    return _style(fig, "3) Clustered Column: High vs Low Counts in Top 4 Genres")


def chart_4_clustered_bar(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("4) Clustered Bar: Avg Danceability vs Energy for Top 5 Artists", "No data")
    top5_artists = df["artists"].value_counts().head(5).index
    subset = df[df["artists"].isin(top5_artists)]
    grouped = (
        subset.groupby("artists", as_index=False)[["danceability", "energy"]]
        .mean()
        .melt(id_vars="artists", var_name="metric", value_name="value")
    )
    fig = px.bar(
        grouped,
        x="value",
        y="artists",
        color="metric",
        orientation="h",
        barmode="group",
        color_discrete_map={"danceability": SPOTIFY_GREEN, "energy": SPOTIFY_PURPLE},
        labels=LABELS,
    )
    return _style(fig, "4) Clustered Bar: Avg Danceability vs Energy for Top 5 Artists")


def chart_5_stacked_column(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("5) Stacked Column: Popularity Mix in Top 5 Genres", "No data")
    top5 = df["track_genre"].value_counts().head(5).index
    subset = df[df["track_genre"].isin(top5)]
    grouped = subset.groupby(["track_genre", "Popularity_Category"], as_index=False).size().rename(columns={"size": "count"})
    fig = px.bar(
        grouped,
        x="track_genre",
        y="count",
        color="Popularity_Category",
        barmode="stack",
        category_orders={"Popularity_Category": CATEGORY_ORDER},
        color_discrete_map={"Low": SPOTIFY_PURPLE, "Medium": "#64748B", "High": SPOTIFY_GREEN},
        labels=LABELS,
    )
    return _style(fig, "5) Stacked Column: Popularity Mix in Top 5 Genres")


def chart_6_stacked_bar(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("6) Stacked Bar: Popularity Mix Across Years", "No data")
    focus_years = [2020, 2021, 2022]
    available = [y for y in focus_years if y in df["Year"].unique()]
    if not available:
        available = sorted(df["Year"].unique())[-3:]
    subset = df[df["Year"].isin(available)]
    grouped = subset.groupby(["Year", "Popularity_Category"], as_index=False).size().rename(columns={"size": "count"})
    fig = px.bar(
        grouped,
        x="count",
        y="Year",
        color="Popularity_Category",
        orientation="h",
        barmode="stack",
        category_orders={"Popularity_Category": CATEGORY_ORDER},
        color_discrete_map={"Low": SPOTIFY_PURPLE, "Medium": "#64748B", "High": SPOTIFY_GREEN},
        labels=LABELS,
    )
    return _style(fig, "6) Stacked Bar: Popularity Mix Across Years")


def chart_7_scatter(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("7) Scatter: Energy vs Valence by Popularity Category", "No data")
    fig = px.scatter(
        df,
        x="energy",
        y="valence",
        color="Popularity_Category",
        opacity=0.65,
        color_discrete_map={"Low": SPOTIFY_PURPLE, "Medium": "#64748B", "High": SPOTIFY_GREEN},
        hover_data=["track_name", "artists", "track_genre", "popularity"],
        render_mode="webgl",
        labels=LABELS,
    )
    return _style(fig, "7) Scatter: Energy vs Valence by Popularity Category")


def chart_8_bubble(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("8) Bubble: Danceability vs Popularity (Size = Duration, Color = Genre)", "No data")
    preferred = ["pop", "rock", "hip-hop", "hip hop"]
    available = {g.lower(): g for g in df["track_genre"].dropna().unique()}
    selected = [available[p] for p in preferred if p in available][:3]
    if len(selected) < 3:
        selected = df["track_genre"].value_counts().head(3).index.tolist()

    subset = df[df["track_genre"].isin(selected)].copy()
    subset["duration_min"] = (subset["duration_ms"] / 60000).clip(0.8, 10)
    fig = px.scatter(
        subset,
        x="danceability",
        y="popularity",
        size="duration_min",
        size_max=45,
        color="track_genre",
        opacity=0.65,
        hover_data=["track_name", "artists", "duration_min"],
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels=LABELS,
    )
    return _style(fig, "8) Bubble: Danceability vs Popularity (Size = Duration, Color = Genre)")


def chart_9_histogram(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("9) Histogram: Tempo Distribution", "No data")
    fig = px.histogram(
        df,
        x="tempo",
        nbins=40,
        color="Popularity_Category",
        barmode="overlay",
        opacity=0.6,
        category_orders={"Popularity_Category": CATEGORY_ORDER},
        color_discrete_map={"Low": SPOTIFY_PURPLE, "Medium": "#64748B", "High": SPOTIFY_GREEN},
        labels=LABELS,
    )
    return _style(fig, "9) Histogram: Tempo Distribution")


def chart_10_box(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("10) Box: Loudness by Popularity Category", "No data")
    fig = px.box(
        df,
        x="Popularity_Category",
        y="loudness",
        color="Popularity_Category",
        points="outliers",
        category_orders={"Popularity_Category": CATEGORY_ORDER},
        color_discrete_map={"Low": SPOTIFY_PURPLE, "Medium": "#64748B", "High": SPOTIFY_GREEN},
        labels=LABELS,
    )
    return _style(fig, "10) Box: Loudness by Popularity Category")


def chart_11_violin(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("11) Violin: Acousticness by Popularity Category", "No data")
    fig = px.violin(
        df,
        x="Popularity_Category",
        y="acousticness",
        color="Popularity_Category",
        box=True,
        points=False,
        category_orders={"Popularity_Category": CATEGORY_ORDER},
        color_discrete_map={"Low": SPOTIFY_PURPLE, "Medium": "#64748B", "High": SPOTIFY_GREEN},
        labels=LABELS,
    )
    return _style(fig, "11) Violin: Acousticness by Popularity Category")


def chart_12_line(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("12) Line: Average Popularity by Year", "No data")
    grouped = df.groupby("Year", as_index=False)["popularity"].mean().sort_values("Year")
    fig = px.line(grouped, x="Year", y="popularity", markers=True, labels=LABELS)
    fig.update_traces(line={"color": SPOTIFY_GREEN, "width": 3}, marker={"size": 8, "color": SPOTIFY_PURPLE})
    return _style(fig, "12) Line: Average Popularity by Year")


def chart_13_area(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("13) Area: Stacked Track Volume by Popularity Category", "No data")
    grouped = df.groupby(["Year", "Popularity_Category"], as_index=False).size().rename(columns={"size": "count"})
    fig = px.area(
        grouped,
        x="Year",
        y="count",
        color="Popularity_Category",
        category_orders={"Popularity_Category": CATEGORY_ORDER},
        color_discrete_map={"Low": SPOTIFY_PURPLE, "Medium": "#64748B", "High": SPOTIFY_GREEN},
        labels=LABELS,
    )
    return _style(fig, "13) Area: Stacked Track Volume by Popularity Category")


def chart_14_heatmap(df: pd.DataFrame):
    if df.empty:
        return _empty_figure("14) Heatmap: Audio Feature Correlation", "No data")
    cols = ["popularity", "danceability", "energy", "valence", "tempo", "loudness", "acousticness"]
    corr = df[cols].corr(numeric_only=True).round(2)
    fig = px.imshow(
        corr,
        text_auto=True,
        zmin=-1,
        zmax=1,
        color_continuous_scale=["#2e1065", "#0f172a", "#0f766e", "#22c55e"],
        labels={"color": "Correlation"},
    )
    fig.update_layout(coloraxis_colorbar={"title": "Corr"})
    return _style(fig, "14) Heatmap: Audio Feature Correlation")


def _card(graph_id: str, fig):
    return html.Div(
        dcc.Graph(id=graph_id, figure=fig, config={"displaylogo": False}),
        style={
            "background": CARD_COLOR,
            "border": "1px solid rgba(56, 189, 248, 0.22)",
            "borderRadius": "16px",
            "backdropFilter": "blur(8px)",
            "padding": "6px",
            "boxShadow": "0 18px 40px rgba(15, 23, 42, 0.28)",
        },
    )


def _top_tracks(df: pd.DataFrame) -> list[dict[str, str | int | float]]:
    # Build compact top-tracks table sorted by popularity and engagement features.
    if df.empty:
        return []
    top = (
        df[["track_name", "artists", "track_genre", "Year", "popularity", "danceability", "energy"]]
        .sort_values(["popularity", "energy", "danceability"], ascending=False)
        .head(12)
        .copy()
    )
    top["danceability"] = top["danceability"].round(3)
    top["energy"] = top["energy"].round(3)
    return top.to_dict("records")


DATA = _load_data()
ALL_GENRES = sorted(DATA["track_genre"].dropna().unique().tolist())
YEAR_MIN = int(DATA["Year"].min())
YEAR_MAX = int(DATA["Year"].max())

slider_min = YEAR_MIN
slider_max = YEAR_MAX
if slider_min == slider_max:
    slider_min = YEAR_MIN - 1
    slider_max = YEAR_MAX + 1


def _year_marks(start: int, end: int):
    span = max(1, end - start)
    if span <= 8:
        years = list(range(start, end + 1))
    else:
        ticks = 6
        years = sorted({start + round(i * span / (ticks - 1)) for i in range(ticks)} | {start, end})
    return {y: {"label": str(y), "style": {"color": MUTED_TEXT, "fontSize": "11px"}} for y in years}


app = Dash(__name__)
app.title = "5*A"
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
        <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
        <link href=\"https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Space+Grotesk:wght@500;700&display=swap\" rel=\"stylesheet\">
        <style>
            body {
                margin: 0;
                background:
                    radial-gradient(900px 460px at 15% -20%, rgba(20, 184, 166, 0.18), transparent 65%),
                    radial-gradient(820px 420px at 110% 10%, rgba(249, 115, 22, 0.18), transparent 60%),
                    linear-gradient(145deg, #040712 0%, #091126 45%, #111827 100%);
            }
            * {
                font-family: 'Manrope', 'Space Grotesk', 'Segoe UI', sans-serif;
            }
            .rc-slider-mark-text {
                color: #94A3B8 !important;
                font-size: 12px;
            }
            .rc-slider-mark-text-active {
                color: #E5E7EB !important;
            }
            .rc-slider-mark {
                margin-top: 2px;
            }
            .rc-slider-track {
                background-color: #14B8A6;
            }
            .rc-slider-rail {
                background-color: rgba(148, 163, 184, 0.35);
            }
            .rc-slider-handle {
                border: 2px solid #22D3EE;
                background-color: #0B1326;
                box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.22);
            }
            .Select-control,
            .Select-menu-outer,
            .Select-menu,
            .Select-value-label,
            .Select-placeholder,
            .Select input {
                background-color: #0B1326 !important;
                color: #E5E7EB !important;
                border-color: rgba(56, 189, 248, 0.25) !important;
            }
            .control-dropdown .Select-control {
                background-color: #0B1326 !important;
                border: 1px solid rgba(56, 189, 248, 0.35) !important;
                border-radius: 10px !important;
                min-height: 48px !important;
                padding: 4px 8px !important;
            }
            .control-dropdown .Select-input > input::placeholder {
                color: #94A3B8 !important;
                font-size: 14px !important;
            }
            .control-dropdown .Select-input > input {
                padding: 6px 8px !important;
                font-size: 14px !important;
                color: #E5E7EB !important;
            }
            .control-dropdown .Select-menu-outer,
            .control-dropdown .Select-menu {
                background-color: #0B1326 !important;
                border: 1px solid rgba(56, 189, 248, 0.35) !important;
                z-index: 2200 !important;
                max-height: 250px !important;
            }
            .control-dropdown .VirtualizedSelectOption,
            .control-dropdown .Select-option {
                background-color: #0B1326 !important;
                color: #E5E7EB !important;
                padding: 10px 12px !important;
                font-size: 14px !important;
            }
            .control-dropdown .VirtualizedSelectFocusedOption,
            .control-dropdown .Select-option.is-focused {
                background-color: #13223d !important;
                color: #ffffff !important;
            }
            .control-dropdown .Select-value-label,
            .control-dropdown .Select-placeholder,
            .control-dropdown .Select-input > input {
                color: #E5E7EB !important;
                font-size: 14px !important;
            }
            .control-dropdown .Select-value,
            .control-dropdown .Select-value span,
            .control-dropdown .Select-arrow-zone,
            .control-dropdown .Select-clear-zone {
                background-color: #0B1326 !important;
                color: #E5E7EB !important;
            }
            .control-radio label {
                color: #E5E7EB !important;
                font-weight: 600 !important;
                display: inline-flex !important;
                align-items: center !important;
                gap: 6px !important;
                margin-right: 14px !important;
            }
            .control-radio input[type="radio"] {
                accent-color: #14B8A6;
            }
            input[type="text"]::placeholder {
                color: #94A3B8 !important;
                opacity: 1;
            }
            @media (max-width: 1200px) {
                #control-grid {
                    grid-template-columns: repeat(2, 1fr) !important;
                }
            }
            @media (max-width: 768px) {
                #control-grid {
                    grid-template-columns: 1fr !important;
                    gap: 12px !important;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

app.layout = html.Div(
        style={"backgroundColor": "transparent", "minHeight": "100vh", "padding": "22px", "color": TEXT_COLOR},
    children=[
        html.H1(
                        "5*A",
                        style={"textAlign": "center", "marginBottom": "6px", "color": TEXT_COLOR, "fontWeight": "800", "letterSpacing": "0.3px", "fontSize": "2.2rem"},
        ),
                html.Div(
                        "Clean multi-year analytics for popularity, behavior, and genre patterns",
                        style={"textAlign": "center", "marginBottom": "16px", "color": MUTED_TEXT, "fontSize": "1rem"},
                ),
        html.Div(
            id="control-grid",
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(280px, 1fr))",
                                "gap": "16px",
                "background": CARD_COLOR,
                                "padding": "18px",
                                "border": "1px solid rgba(56, 189, 248, 0.22)",
                                "borderRadius": "16px",
                                "backdropFilter": "blur(8px)",
                                "marginBottom": "18px",
            },
            children=[
                html.Div(
                    children=[
                                                html.Label("Genre", style={"color": ACCENT_SOFT, "fontWeight": "700", "marginBottom": "6px", "display": "block"}),
                        dcc.Dropdown(
                            id="genre-dropdown",
                            className="control-dropdown",
                            options=[{"label": "All", "value": "All"}] + [{"label": g, "value": g} for g in ALL_GENRES],
                            value="All",
                            clearable=False,
                            maxHeight=180,
                            style={
                                "color": TEXT_COLOR,
                                "fontWeight": "600",
                                "backgroundColor": INPUT_BG,
                                "borderRadius": "10px",
                            },
                        ),
                    ]
                ),
                html.Div(
                    children=[
                                                html.Label("Year Range", style={"color": ACCENT_SOFT, "fontWeight": "700", "marginBottom": "6px", "display": "block"}),
                        dcc.RangeSlider(
                            id="year-slider",
                            min=slider_min,
                            max=slider_max,
                            value=[YEAR_MIN, YEAR_MAX],
                            allowCross=False,
                            marks=_year_marks(slider_min, slider_max),
                            tooltip={"placement": "bottom", "always_visible": False},
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Label("Popularity Scope", style={"color": ACCENT_SOFT, "fontWeight": "700", "marginBottom": "6px", "display": "block"}),
                        dcc.RadioItems(
                            id="popularity-radio",
                            className="control-radio",
                            options=[
                                {"label": "All", "value": "All"},
                                {"label": "High Popularity", "value": "High"},
                                {"label": "Low Popularity", "value": "Low"},
                            ],
                            value="All",
                            inline=True,
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Label("Search", style={"color": ACCENT_SOFT, "fontWeight": "700", "marginBottom": "6px", "display": "block"}),
                        dcc.Input(
                            id="track-search",
                            type="text",
                            placeholder="Track or artist",
                            debounce=True,
                            style={
                                "width": "100%",
                                "background": INPUT_BG,
                                "border": "1px solid rgba(56, 189, 248, 0.22)",
                                "borderRadius": "10px",
                                "padding": "10px 12px",
                                "color": TEXT_COLOR,
                                "fontWeight": "600",
                            },
                        ),
                    ]
                ),
            ],
        ),
        html.Div(
            style={"display": "flex", "justifyContent": "flex-end", "gap": "12px", "marginBottom": "16px"},
            children=[
                html.A(
                    html.Button(
                        "Search in 5A_Search",
                        id="search-5a-btn",
                        style={
                            "background": "linear-gradient(135deg, #F97316 0%, #FB923C 100%)",
                            "color": "#fff",
                            "border": "none",
                            "fontWeight": "800",
                            "padding": "10px 14px",
                            "borderRadius": "10px",
                            "cursor": "pointer",
                        },
                    ),
                    id="search-5a-link",
                    href="http://127.0.0.1:5173",
                    target="_blank",
                    style={"textDecoration": "none"},
                ),
                html.Button(
                    "Download Filtered CSV",
                    id="download-btn",
                    n_clicks=0,
                    style={
                        "background": "linear-gradient(135deg, #14B8A6 0%, #0EA5E9 100%)",
                        "color": "#001E2B",
                        "border": "none",
                        "fontWeight": "800",
                        "padding": "10px 14px",
                        "borderRadius": "10px",
                        "cursor": "pointer",
                    },
                ),
                dcc.Download(id="download-data"),
            ],
        ),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "12px", "marginBottom": "14px"},
            children=[
                html.Div([html.Div("Tracks in View", style={"color": MUTED_TEXT}), html.Div(id="kpi-tracks", style={"fontSize": "28px", "fontWeight": "800", "color": ACCENT_PRIMARY})], style={"background": CARD_COLOR, "border": "1px solid rgba(56, 189, 248, 0.22)", "borderRadius": "16px", "padding": "12px", "backdropFilter": "blur(8px)"}),
                html.Div([html.Div("Average Popularity", style={"color": MUTED_TEXT}), html.Div(id="kpi-pop", style={"fontSize": "28px", "fontWeight": "800", "color": ACCENT_PRIMARY})], style={"background": CARD_COLOR, "border": "1px solid rgba(56, 189, 248, 0.22)", "borderRadius": "16px", "padding": "12px", "backdropFilter": "blur(8px)"}),
                html.Div([html.Div("Top Genre", style={"color": MUTED_TEXT}), html.Div(id="kpi-genre", style={"fontSize": "28px", "fontWeight": "800", "color": ACCENT_PRIMARY})], style={"background": CARD_COLOR, "border": "1px solid rgba(56, 189, 248, 0.22)", "borderRadius": "16px", "padding": "12px", "backdropFilter": "blur(8px)"}),
                html.Div([html.Div("Top Artist", style={"color": MUTED_TEXT}), html.Div(id="kpi-artist", style={"fontSize": "28px", "fontWeight": "800", "color": ACCENT_PRIMARY})], style={"background": CARD_COLOR, "border": "1px solid rgba(56, 189, 248, 0.22)", "borderRadius": "16px", "padding": "12px", "backdropFilter": "blur(8px)"}),
                html.Div([html.Div("Year Span", style={"color": MUTED_TEXT}), html.Div(id="kpi-years", style={"fontSize": "28px", "fontWeight": "800", "color": ACCENT_PRIMARY})], style={"background": CARD_COLOR, "border": "1px solid rgba(56, 189, 248, 0.22)", "borderRadius": "16px", "padding": "12px", "backdropFilter": "blur(8px)"}),
            ],
        ),
        html.Div(id="insight-line", style={"marginBottom": "18px", "padding": "14px", "background": CARD_COLOR, "border": "1px solid rgba(56, 189, 248, 0.22)", "borderRadius": "16px", "lineHeight": "1.65", "color": TEXT_COLOR, "backdropFilter": "blur(8px)", "whiteSpace": "normal", "wordWrap": "break-word", "minHeight": "56px", "fontSize": "15px"}),
        html.H3("Comparison View", style={"color": ACCENT_SECONDARY, "fontWeight": "800", "marginBottom": "8px"}),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(330px, 1fr))", "gap": "14px", "marginBottom": "16px"},
            children=[
                _card("chart-1", chart_1_top5_genres(DATA)),
                _card("chart-2", chart_2_bottom5_genres(DATA)),
                _card("chart-3", chart_3_clustered_column(DATA)),
                _card("chart-4", chart_4_clustered_bar(DATA)),
                _card("chart-5", chart_5_stacked_column(DATA)),
                _card("chart-6", chart_6_stacked_bar(DATA)),
            ],
        ),
        html.H3("Relationship View", style={"color": ACCENT_SECONDARY, "fontWeight": "800", "marginBottom": "8px"}),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(380px, 1fr))", "gap": "14px", "marginBottom": "16px"},
            children=[
                _card("chart-7", chart_7_scatter(DATA)),
                _card("chart-8", chart_8_bubble(DATA)),
            ],
        ),
        html.H3("Distribution View", style={"color": ACCENT_SECONDARY, "fontWeight": "800", "marginBottom": "8px"}),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(330px, 1fr))", "gap": "14px", "marginBottom": "16px"},
            children=[
                _card("chart-9", chart_9_histogram(DATA)),
                _card("chart-10", chart_10_box(DATA)),
                _card("chart-11", chart_11_violin(DATA)),
            ],
        ),
        html.H3("Time Series View", style={"color": ACCENT_SECONDARY, "fontWeight": "800", "marginBottom": "8px"}),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(380px, 1fr))", "gap": "14px", "marginBottom": "16px"},
            children=[
                _card("chart-12", chart_12_line(DATA)),
                _card("chart-13", chart_13_area(DATA)),
            ],
        ),
        html.H3("Feature Correlation", style={"color": ACCENT_SECONDARY, "fontWeight": "800", "marginBottom": "8px"}),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr", "gap": "14px", "marginBottom": "16px"},
            children=[
                _card("chart-14", chart_14_heatmap(DATA)),
            ],
        ),
        html.H3("Top Tracks Snapshot", style={"color": ACCENT_SECONDARY, "fontWeight": "800", "marginBottom": "8px"}),
        html.Div(
            style={"background": CARD_COLOR, "border": "1px solid rgba(56, 189, 248, 0.22)", "borderRadius": "16px", "padding": "10px", "backdropFilter": "blur(8px)"},
            children=[
                dash_table.DataTable(
                    id="top-tracks-table",
                    columns=[
                        {"name": "Track", "id": "track_name"},
                        {"name": "Artist", "id": "artists"},
                        {"name": "Genre", "id": "track_genre"},
                        {"name": "Year", "id": "Year"},
                        {"name": "Popularity", "id": "popularity"},
                        {"name": "Danceability", "id": "danceability"},
                        {"name": "Energy", "id": "energy"},
                    ],
                    data=_top_tracks(DATA),
                    page_size=12,
                    sort_action="native",
                    style_as_list_view=True,
                    style_table={"overflowX": "auto", "borderRadius": "12px"},
                    style_header={"backgroundColor": "#0B1326", "color": ACCENT_SOFT, "fontWeight": "700", "border": "none"},
                    style_cell={"backgroundColor": "rgba(11, 19, 38, 0.95)", "color": TEXT_COLOR, "border": "none", "fontSize": "13px", "padding": "10px", "maxWidth": "220px", "whiteSpace": "normal"},
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "rgba(15, 23, 42, 0.85)"}
                    ],
                )
            ],
        ),
    ],
)


@app.callback(
    Output("kpi-tracks", "children"),
    Output("kpi-pop", "children"),
    Output("kpi-genre", "children"),
    Output("kpi-artist", "children"),
    Output("kpi-years", "children"),
    Output("insight-line", "children"),
    Output("chart-1", "figure"),
    Output("chart-2", "figure"),
    Output("chart-3", "figure"),
    Output("chart-4", "figure"),
    Output("chart-5", "figure"),
    Output("chart-6", "figure"),
    Output("chart-7", "figure"),
    Output("chart-8", "figure"),
    Output("chart-9", "figure"),
    Output("chart-10", "figure"),
    Output("chart-11", "figure"),
    Output("chart-12", "figure"),
    Output("chart-13", "figure"),
    Output("chart-14", "figure"),
    Output("top-tracks-table", "data"),
    Input("genre-dropdown", "value"),
    Input("year-slider", "value"),
    Input("popularity-radio", "value"),
    Input("track-search", "value"),
)
def update_dashboard(genre: str, year_range: list[int], scope: str, search_text: str | None):
    # Single callback keeps all major visuals synchronized with shared filters.
    view = _filtered_view(DATA, genre, year_range, scope, search_text)
    tracks, avg_pop, top_genre, top_artist, years, insight = _kpis(view)
    return (
        tracks,
        avg_pop,
        top_genre,
        top_artist,
        years,
        insight,
        chart_1_top5_genres(view),
        chart_2_bottom5_genres(view),
        chart_3_clustered_column(view),
        chart_4_clustered_bar(view),
        chart_5_stacked_column(view),
        chart_6_stacked_bar(view),
        chart_7_scatter(view),
        chart_8_bubble(view),
        chart_9_histogram(view),
        chart_10_box(view),
        chart_11_violin(view),
        chart_12_line(view),
        chart_13_area(view),
        chart_14_heatmap(view),
        _top_tracks(view),
    )


@app.callback(
    Output("search-5a-link", "href"),
    Input("genre-dropdown", "value"),
    prevent_initial_call=False,
)
def update_search_link(genre: str):
    # Generate 5A_Search link with artist from selected genre.
    base_url = "http://127.0.0.1:5173"
    if genre and genre != "All":
        top_artist = DATA[DATA["track_genre"] == genre]["artists"].value_counts().index[0] if not DATA[DATA["track_genre"] == genre].empty else ""
        if top_artist:
            return f"{base_url}?search={top_artist}"
    return base_url


@app.callback(
    Output("download-data", "data"),
    Input("download-btn", "n_clicks"),
    State("genre-dropdown", "value"),
    State("year-slider", "value"),
    State("popularity-radio", "value"),
    State("track-search", "value"),
    prevent_initial_call=True,
)
def download_filtered_data(n_clicks: int, genre: str, year_range: list[int], scope: str, search_text: str | None):
    # Export only the currently filtered view to keep analysis reproducible.
    if not n_clicks:
        return no_update
    view = _filtered_view(DATA, genre, year_range, scope, search_text)
    cols = [
        "track_name",
        "artists",
        "track_genre",
        "Year",
        "popularity",
        "danceability",
        "energy",
        "valence",
        "tempo",
        "loudness",
        "acousticness",
        "duration_ms",
        "Popularity_Category",
    ]
    export_cols = [c for c in cols if c in view.columns]
    return dcc.send_data_frame(view[export_cols].to_csv, "spotify_filtered_view.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--host", type=str, default=None)
    parser.add_argument("--port", type=int, default=None)
    args, _ = parser.parse_known_args()

    host = args.host or os.getenv("HOST", "127.0.0.1")
    port = args.port or int(os.getenv("PORT", "8050"))
    app.run(debug=True, host=host, port=port)
