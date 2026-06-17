import os
from dash import Dash, html

from layout import create_layout
from callbacks.overview import register_overview_callbacks
from callbacks.mrna import register_mrna_callbacks
from callbacks.mutation import register_mutation_callbacks
from callbacks.co import register_co_callbacks
from cache import cache_manager


app = Dash(
    __name__,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes",
        },
        {
            "name": "description",
            "content": "METABRIC Breast Cancer Dashboard - Interactive data visualization and analysis",
        },
        {
            "name": "theme-color",
            "content": "#1f77b4",
        },
    ],
    suppress_callback_exceptions=True,
)

server = app.server
app.title = "METABRIC Breast Cancer Dashboard"

# Enable caching by default
cache_manager.enable()

# Layout
app.layout = create_layout()

# Callbacks
register_overview_callbacks(app)
register_mrna_callbacks(app)
register_mutation_callbacks(app)
register_co_callbacks(app)


if __name__ == "__main__":
    debug_mode = os.getenv("DASH_DEBUG", "False").lower() == "true"
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("DASH_PORT", 8050)),
        debug=debug_mode,
    )
