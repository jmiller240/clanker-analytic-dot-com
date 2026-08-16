# NFL Analytics Dashboard

An interactive, mobile-friendly NFL stats dashboard built with Plotly Dash.
Started as an MVP; intended to grow throughout an MS in Data Science into a
full portfolio piece (more sports, models, and views over time).

## What's here right now

- A season/position/stat leaderboard chart, fully interactive (Plotly).
- Data pulled from [nflverse](https://github.com/nflverse) via `nfl_data_py`,
  cached locally as parquet so repeat loads are fast.
- Responsive layout via `dash-bootstrap-components` — usable on phones.

## Quickstart

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open http://localhost:8050 in your browser (or on your phone if it's
on the same network, using your machine's local IP).

## Project structure

```
nfl-analytics-app/
├── app.py              # Dash app: layout + callbacks (the UI layer)
├── data/
│   ├── __init__.py
│   ├── loaders.py       # All data access + caching lives here
│   └── cache/            # Cached parquet files (gitignored)
├── requirements.txt
└── README.md
```

**Why this split matters going forward:** `app.py` only knows about
layout and callbacks. `data/loaders.py` only knows about fetching and
shaping data. When you outgrow Dash's UI and want to move to a
FastAPI + React/Next.js stack, the functions in `data/loaders.py` (and
any model code you add later) can be wrapped almost as-is in FastAPI
endpoints — you won't have to rebuild your actual analytics.

## Roadmap / ideas for future coursework tie-ins

- [ ] Add a play-by-play / EPA-based view (`nfl_data_py.import_pbp_data`)
- [ ] Add a simple win-probability or fantasy-points prediction model,
      served through a new callback (stats/ML coursework)
- [ ] Add a "Compare Players" page (multi-page Dash app)
- [ ] Add confidence intervals / uncertainty to any model outputs (stats)
- [ ] Swap heuristic stat rankings for a trained model (ML coursework)
- [ ] Add a second sport (new loader module + sport selector in navbar)
- [ ] Migrate to FastAPI backend + Next.js frontend once the UI needs
      outgrow what Dash comfortably supports
- [ ] Add user accounts / saved views (backend/auth coursework)
- [ ] Deploy properly (Render/Railway) with a real domain

## Deployment (quick option)

This app exposes `server = app.server` (a Flask app), so it's
gunicorn-ready. On Render/Railway, set the start command to:

```bash
gunicorn app:server
```

## Data source

Data comes from the [nflverse](https://github.com/nflverse) project via
`nfl_data_py`. Refresh the cache by deleting files in `data/cache/`.
