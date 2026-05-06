import pandas as pd

from spotify_trends_dashboard.app import _filtered_view, _kpis


def sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "track_name": "Song A",
                "artists": "Artist X",
                "track_genre": "pop",
                "popularity": 80,
                "danceability": 0.8,
                "energy": 0.9,
                "valence": 0.6,
                "tempo": 120,
                "loudness": -5,
                "acousticness": 0.1,
                "duration_ms": 210000,
                "Year": 2022,
                "Popularity_Category": "High",
            },
            {
                "track_name": "Song B",
                "artists": "Artist Y",
                "track_genre": "rock",
                "popularity": 45,
                "danceability": 0.5,
                "energy": 0.6,
                "valence": 0.4,
                "tempo": 140,
                "loudness": -8,
                "acousticness": 0.2,
                "duration_ms": 180000,
                "Year": 2020,
                "Popularity_Category": "Medium",
            },
        ]
    )


def test_filtered_view_by_genre() -> None:
    df = sample_data()
    result = _filtered_view(df, "pop", [2020, 2023], "All", None)

    assert len(result) == 1
    assert result.iloc[0]["track_name"] == "Song A"


def test_filtered_view_search() -> None:
    df = sample_data()
    result = _filtered_view(df, "All", [2020, 2023], "All", "artist y")

    assert len(result) == 1
    assert result.iloc[0]["artists"] == "Artist Y"


def test_kpis_summary() -> None:
    df = sample_data()
    tracks, avg_pop, top_genre, top_artist, years, insight = _kpis(df)

    assert tracks == "2"
    assert avg_pop == "62.5"
    assert years == "2020 - 2022"
    assert "tracks" in insight
