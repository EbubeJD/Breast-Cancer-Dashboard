from dash import html, dcc
from utils import CARD_STYLE, COLORS, CONTAINER_STYLE


def stat_card(title, value):
    """Mobile-friendly stat card with responsive text."""
    return html.Div(
        className="stat-card",
        children=[
            html.Div(title, className="stat-card-label"),
            html.Div(value, className="stat-card-value"),
        ],
    )


def create_layout():
    """Top-level layout with Bootstrap and responsive design."""
    return html.Div(
        className="dashboard-container",
        children=[
            # Viewport meta tag (handled in server configuration)
            # CSS Link
            html.Link(
                rel="stylesheet",
                href="/static/styles.css",
            ),

            # Header
            html.Div(
                className="dashboard-header",
                children=[
                    html.H1("METABRIC Breast Cancer Dashboard", style={"margin": "0 0 0.5rem 0"}),
                    html.P(
                        "Explore clinical attributes, mutation profiles, and mRNA expression.",
                        style={"margin": "0", "color": "#888", "fontSize": "0.95rem"},
                    ),
                ],
            ),

            # Tabs (mobile-responsive)
            html.Div(
                className="tabs-container",
                children=[
                    dcc.Tabs(
                        id="tabs",
                        value="tab-overview",
                        parent_className="tabs-list",
                        className="tabs-list",
                        children=[
                            dcc.Tab(
                                label="Overview",
                                value="tab-overview",
                                className="tab-button",
                                selected_className="tab-button active",
                            ),
                            dcc.Tab(
                                label="Mutations",
                                value="tab-mutations",
                                className="tab-button",
                                selected_className="tab-button active",
                            ),
                            dcc.Tab(
                                label="mRNA",
                                value="tab-mrna",
                                className="tab-button",
                                selected_className="tab-button active",
                            ),
                            dcc.Tab(
                                label="Co-Analysis",
                                value="tab-comutation",
                                className="tab-button",
                                selected_className="tab-button active",
                            ),
                        ],
                    )
                ],
            ),

            # Tab Content
            html.Div(
                id="tab-content",
                className="tab-content",
                style={"padding": "0"},
            ),
        ],
    )
