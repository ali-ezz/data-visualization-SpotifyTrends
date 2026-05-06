# Enterprise Airline Attendance Big Data Pipeline

A reproducible Spotify trends analytics and local AI search dashboard repository with a polished project structure, governance artifacts, and testing support.

## Overview

This project combines a data cleaning and trend analysis pipeline for Spotify metadata with an interactive Dash dashboard and a local AI-capable search front end. The repository is organized so a stranger can understand, run, and evaluate the project quickly.

## One-line summary

Spotify trends analytics, year extraction, and AI search tooling packaged with professional repo documentation and GitHub workflow artifacts.

## Problem solved

Spotify metadata and popularity data are often noisy, inconsistent, and difficult to analyze at scale. This project provides a reproducible pipeline to clean that data, derive release years, and expose interactive visual analytics for trends, genres, and popularity.

## Features

- Cleaned Spotify dataset preparation and year extraction pipeline
- Interactive Dash dashboard for visual analytics across popularity, genre, and year
- Local AI-ready React/Vite search interface in `5A_Search`
- GitHub-ready repo structure with README, LICENSE, CONTRIBUTING, SECURITY, and CHANGELOG
- Basic unit tests for core data filtering and summary functions
- Environment configuration via `.env.example`

## Tech stack

- Python 3.11+
- Dash, Plotly, Pandas, NumPy
- JupyterLab for notebook-driven ETL
- React, Vite, Tailwind CSS, WebLLM for the search UI
- pytest for automated testing

## Live demo link

No public live demo is available for this repository.

## Installation

```bash
git clone https://github.com/ali-ezz/enterprise-airline-attendance-big-data-pipeline.git
cd enterprise-airline-attendance-big-data-pipeline
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Run the Dash dashboard

```bash
python spotify_trends_dashboard/app.py
```

### Run the search front-end

```bash
cd 5A_Search
npm install
npm run dev
```

### Run the notebook pipeline

Open `spotify_trends_dashboard/five_a_data_prep.ipynb` in JupyterLab and execute the notebook sequentially to produce the cleaned output dataset.

## Project structure

- `5A_Search/` — React/Vite local AI search front-end
- `spotify_trends_dashboard/` — Dash analytics app and ETL notebook
- `assets/` — repository asset placeholder
- `tests/` — unit tests
- `requirements.txt` — Python dependencies
- `.env.example` — sample environment variable configuration
- `.github/` — issue and PR templates
- `LICENSE` — project license
- `README.md` — project documentation

## Environment variables

Create a `.env` file or export the following values before running the notebook pipeline:

```text
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
MB_MAX_LOOKUPS=120
```

## Results and metrics

- Cleaned Spotify dataset: `spotify_trends_dashboard/dataset_5a/spotify_cleaned.csv`
- Final cleaned dataset contains over 100,000 rows after filtering and deduplication
- Popularity categories: Low, Medium, High
- Year range: 1900 to 2035

## Roadmap

- Add data versioning and schema validation
- Add deployment documentation for the Dash app
- Add end-to-end notebook execution tests
- Add a dedicated `notebooks/` folder for exploratory analysis and data lineage

## Credits

- Core data pipeline and dashboard implementation in `spotify_trends_dashboard`
- Search UI implementation in `5A_Search`
- Project structure and governance artifacts added for repo professionalism

## License

This project is licensed under the MIT License. See `LICENSE` for details.
