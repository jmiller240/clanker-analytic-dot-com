
import dash
from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc


# --------- Setup -----------

dash.register_page(__name__, path = '/')


# --------- Main Layout ---------

layout = dbc.Container(
    [
        html.Div(
            'Welcome to Clanker Analytic',
            style={
                'fontSize': '24px',
            }
        ),
    ],
    fluid=True
)