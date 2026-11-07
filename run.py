import os

from quiron.server import create_app


dashboard = create_app()
app = dashboard.server
server = app


if __name__ == "__main__":
    dashboard.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8050")),
    )