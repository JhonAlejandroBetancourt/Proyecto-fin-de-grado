from quiron.server import create_app


app = create_app()
server = app.server


if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=8050,
    )