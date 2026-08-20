"""
NFL Analytics Dashboard — MVP

A starting point meant to grow. Structure notes for future-you:
- All data access goes through data/loaders.py, not directly in callbacks.
- Add new "pages" as new files under pages/ once this grows past one view
  (Dash has built-in multi-page support via dash.register_page).
- Add new sports by adding new loader modules (data/nba_loaders.py, etc.)
  and a sport selector in the navbar.
"""

import polars as pl

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

import plotly.express as px
import plotly.io as pio

from assets.plotly_theme import nfl_template

pio.templates['nfl_template'] = nfl_template



# -------- App ---------

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    use_pages = True,
    meta_tags=[
        # Required for real mobile responsiveness — without this, mobile
        # browsers render the page zoomed-out at desktop width.
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    title="NFL Analytics",
)
server = app.server  # exposed for deployment (gunicorn looks for this)


# ---------- Layout ----------

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.NavItem(dbc.NavLink("League", href="/league")),
        dbc.NavItem(dbc.NavLink("Teams", href="/teams")),
        dbc.NavItem(dbc.NavLink("Players", href="/stat_leaders")),
        dbc.NavItem(dbc.NavLink("Matchups", href="/matchups")),
    ],
    brand="🏈 Clanker Analytic",
    brand_href="/",
    color="primary",
    dark=True,
    fluid=True,
)

app.layout = dbc.Container(
    [
        navbar, 
        dash.page_container,
        html.Hr(),
        html.P(
            "Data: nflverse (via nfl_data_py). Built as an ongoing "
            "learning project — more sports, models, and views coming.",
            className="text-muted small text-center",
        ),
    ],
    fluid = True
)



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
