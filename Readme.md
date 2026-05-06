# Spotify Trends Dashboard and Nevai Search

A combined data visualization and search dashboard repository that includes a Spotify trend analytics pipeline plus a local AI-enhanced search front-end.

> Recommended GitHub repo name: `enterprise-airline-attendance-big-data-pipeline`

## One-line summary

Interactive Spotify analytics and trend exploration with a production-style dashboard, notebook ETL pipeline, and React/Vite search interface.

## Problem solved

This repository makes Spotify listening trends accessible through a clean analytics dashboard and a reproducible data pipeline, while preserving the ability to run a separate minimal search UI for fast exploration.

## Features

- Data cleaning and year extraction pipeline for Spotify track metadata
- Interactive Dash dashboard for Spotify popularity, genre, tempo, and year-based analytics
- Notebook-driven ETL with reproducible output generation
- Local AI-capable React/Vite meta-search front-end in `5A_Search`
- Built-in support for Spotify and MusicBrainz enrichment
- Basic unit tests for core data helper functions

## Tech stack

- Python 3.11+
- Dash, Plotly, Pandas, NumPy, JupyterLab
- React, Vite, Tailwind CSS, WebLLM
- pytest for tests

## Installation

### Python environment

1. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install Python dependencies.

```bash
pip install -r requirements.txt
```

3. Install frontend dependencies for the search app.

```bash
cd 5A_Search
npm install
```

## Usage

### Run the Spotify Trends dashboard

```bash
python spotify_trends_dashboard/app.py
```

Then open the Dash app at the local host URL printed by Dash.

### Run the search front-end

```bash
cd 5A_Search
npm run dev
```

Then open the Vite preview URL shown in the terminal.

### Run the notebook pipeline

Open `spotify_trends_dashboard/five_a_data_prep.ipynb` in JupyterLab and execute the cells sequentially.

## Project structure

- `5A_Search/`: React/Vite search experience and UI
- `spotify_trends_dashboard/`: Spotify analytics dashboard and ETL notebook
- `dataset.csv`: raw input dataset for preprocessing
- `README.md`: project overview and setup instructions
- `requirements.txt`: Python dependencies
- `tests/`: unit tests for Python helper logic
- `.env.example`: expected environment variables
- `LICENSE`: project license
- `.gitignore`: ignored artifacts and build output
- `.github/`: issue and PR templates

## Environment variables

Create a `.env` file or export these environment variables before running the notebook pipeline.

```text
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
MB_MAX_LOOKUPS=120
```

Notes:
- `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are optional; if unset, the pipeline skips Spotify API enrichment and continues with cached or fallback data.
- `MB_MAX_LOOKUPS` controls how many MusicBrainz lookups are allowed during year extraction.

## Results / metrics

- Final cleaned dataset: `spotify_trends_dashboard/dataset_5a/spotify_cleaned.csv`
- Dataset size: 113,382 rows after cleaning and deduplication
- Popularity categories: Low, Medium, High
- Year range: 1900 to 2035

## Roadmap

- Add a dedicated `notebooks/` folder for DS artifacts and exploratory analysis
- Add dashboard deployment instructions and Docker support
- Add end-to-end tests for notebook pipelines and app startup behavior
- Add data versioning and schema validation

## Credits

- Built from the existing Spotify Trends Dashboard data pipeline and Nevai Search UI codebase
- Dashboard powered by Dash and Plotly
- Search UI powered by React, Vite, and WebLLM

## License

This project is licensed under the MIT License. See `LICENSE` for details.
