"""Pruebas del punto de entrada WSGI utilizado por Vercel."""

import run


def test_vercel_entrypoint_exposes_wsgi_application():
    assert run.app is run.server
    assert callable(run.app)


def test_vercel_wsgi_application_serves_dashboard():
    response = run.app.test_client().get("/")

    assert response.status_code == 200
    assert b"<html" in response.data.lower()
