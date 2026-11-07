import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from flask import Flask, jsonify

from quiron import auth
from quiron.server import create_app


def _set_auth_environment(monkeypatch):
    values = {
        "QUIRON_AUTH_ENABLED": "1",
        "SUPABASE_URL": "https://quiron-test.supabase.co",
        "SUPABASE_ANON_KEY": "public-test-key",
        "SUPABASE_SERVICE_ROLE_KEY": "service-test-key",
        "QUIRON_BASE_URL": "http://localhost:5000",
        "QUIRON_ADMIN_EMAILS": "admin@example.com",
        "QUIRON_GOOGLE_ALLOWED_EMAILS": "google@example.com",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def _claims(
    *,
    email="user@example.com",
    role="user",
    providers=None,
    aal="aal2",
):
    return {
        "sub": "user-id",
        "email": email,
        "aal": aal,
        "exp": int(time.time()) + 600,
        "app_metadata": {
            "role": role,
            "providers": providers or ["email"],
        },
    }


def _create_app(monkeypatch, claims=None):
    _set_auth_environment(monkeypatch)
    flask_app = Flask(__name__)
    auth.register_auth(flask_app)
    flask_app.add_url_rule(
        "/protected",
        endpoint="protected",
        view_func=lambda: "contenido protegido",
    )
    flask_app.add_url_rule(
        "/_dash-layout",
        endpoint="dash_layout",
        view_func=lambda: jsonify({"layout": "protected"}),
    )
    if claims is not None:
        monkeypatch.setattr(
            auth,
            "_verify_access_token",
            lambda token, settings, client: claims,
        )
    return flask_app


def _login(client, token="valid"):
    return client.post(
        "/auth/session",
        json={"access_token": token},
        headers={"Origin": "http://localhost:5000"},
    )


def test_auth_is_disabled_by_default_outside_vercel(monkeypatch):
    monkeypatch.delenv("QUIRON_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    flask_app = Flask(__name__)

    auth.register_auth(flask_app)

    assert flask_app.config["QUIRON_AUTH_ENABLED"] is False
    assert flask_app.test_client().get("/login").status_code == 404


def test_vercel_auth_fails_closed_when_configuration_is_missing(
    monkeypatch,
):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("QUIRON_AUTH_ENABLED", "0")
    monkeypatch.delenv("SUPABASE_URL", raising=False)

    with pytest.raises(auth.AuthConfigurationError):
        auth.load_auth_settings()


def test_supabase_admin_request_uses_bearer_service_key(monkeypatch):
    _set_auth_environment(monkeypatch)
    settings = auth.load_auth_settings()
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b"{}"

    def fake_urlopen(request, timeout):
        captured["authorization"] = request.get_header(
            "Authorization"
        )
        captured["api_key"] = request.get_header("Apikey")
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(auth, "urlopen", fake_urlopen)

    auth._supabase_request(
        settings,
        "/auth/v1/admin/users",
        admin=True,
    )

    assert captured == {
        "authorization": "Bearer service-test-key",
        "api_key": "service-test-key",
        "timeout": 12,
    }


def test_auth_enabled_requires_an_origin_only_base_url(monkeypatch):
    _set_auth_environment(monkeypatch)
    monkeypatch.setenv(
        "QUIRON_BASE_URL",
        "https://quiron.example.com/path",
    )

    with pytest.raises(auth.AuthConfigurationError):
        auth.load_auth_settings()


def test_access_token_signature_issuer_and_audience_are_verified(
    monkeypatch,
):
    _set_auth_environment(monkeypatch)
    settings = auth.load_auth_settings()
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    jwks_client = SimpleNamespace(
        get_signing_key_from_jwt=lambda token: SimpleNamespace(
            key=private_key.public_key(),
            algorithm_name="RS256",
        )
    )
    claims = _claims()
    claims.update(
        {
            "iss": f"{settings.supabase_url}/auth/v1",
            "aud": "authenticated",
        }
    )
    token = jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
    )

    assert auth._verify_access_token(
        token,
        settings,
        jwks_client,
    )["sub"] == "user-id"

    invalid_claims = {**claims, "aud": "unauthorized"}
    invalid_token = jwt.encode(
        invalid_claims,
        private_key,
        algorithm="RS256",
    )
    with pytest.raises(auth.AuthenticationError):
        auth._verify_access_token(
            invalid_token,
            settings,
            jwks_client,
        )

    wrong_issuer = jwt.encode(
        {**claims, "iss": "https://attacker.example/auth/v1"},
        private_key,
        algorithm="RS256",
    )
    with pytest.raises(auth.AuthenticationError):
        auth._verify_access_token(
            wrong_issuer,
            settings,
            jwks_client,
        )

    other_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    forged_token = jwt.encode(
        claims,
        other_key,
        algorithm="RS256",
    )
    with pytest.raises(auth.AuthenticationError):
        auth._verify_access_token(
            forged_token,
            settings,
            jwks_client,
        )


def test_unauthenticated_dashboard_redirects_to_login(monkeypatch):
    flask_app = _create_app(monkeypatch)
    client = flask_app.test_client()

    response = client.get("/protected")
    dash_response = client.get("/_dash-layout")
    status_response = client.get("/auth/status")

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login?")
    assert dash_response.status_code == 401
    assert status_response.status_code == 401


def test_login_page_is_public_and_does_not_expose_service_key(
    monkeypatch,
):
    flask_app = _create_app(monkeypatch)

    response = flask_app.test_client().get("/login")

    assert response.status_code == 200
    assert b"Quir" in response.data
    assert b"public-test-key" in response.data
    assert b"service-test-key" not in response.data


def test_dash_index_includes_public_auth_config_only(monkeypatch):
    _set_auth_environment(monkeypatch)
    monkeypatch.setattr(
        auth,
        "_verify_access_token",
        lambda token, settings, client: _claims(
            email="admin@example.com",
            role="admin",
        ),
    )
    dash_app = create_app()
    client = dash_app.server.test_client()
    _login(client)

    response = client.get("/")

    assert response.status_code == 200
    assert b'name="supabase-url"' in response.data
    assert b'name="supabase-anon-key"' in response.data
    assert b"auth-session.js" in response.data
    assert b"service-test-key" not in response.data
    assert client.get("/assets/auth-session.js").status_code == 200
    admin_page = client.get("/admin")
    assert admin_page.status_code == 200
    assert b"public-test-key" in admin_page.data
    assert b"service-test-key" not in admin_page.data


def test_session_requires_same_origin_and_mfa(monkeypatch):
    flask_app = _create_app(monkeypatch, _claims(aal="aal1"))
    client = flask_app.test_client()

    cross_origin = client.post(
        "/auth/session",
        json={"access_token": "valid"},
        headers={"Origin": "https://attacker.example"},
    )
    missing_mfa = _login(client)

    assert cross_origin.status_code == 403
    assert missing_mfa.status_code == 403
    assert "quiron_access" not in missing_mfa.headers.get(
        "Set-Cookie",
        "",
    )


def test_session_rejects_non_object_json(monkeypatch):
    flask_app = _create_app(monkeypatch, _claims())

    response = flask_app.test_client().post(
        "/auth/session",
        json=["valid"],
        headers={"Origin": "http://localhost:5000"},
    )

    assert response.status_code == 400


def test_session_cookie_unlocks_protected_dashboard(monkeypatch):
    flask_app = _create_app(monkeypatch, _claims())
    client = flask_app.test_client()

    response = _login(client)

    assert response.status_code == 200
    assert response.json == {
        "email": "user@example.com",
        "is_admin": False,
    }
    assert "HttpOnly" in response.headers["Set-Cookie"]
    assert "SameSite=Lax" in response.headers["Set-Cookie"]
    assert client.get("/protected").data == b"contenido protegido"
    assert client.get("/auth/status").json == {
        "email": "user@example.com",
        "is_admin": False,
    }


def test_google_sign_in_is_limited_to_allowed_accounts(monkeypatch):
    claims = _claims(
        email="other@example.com",
        providers=["google"],
    )
    flask_app = _create_app(monkeypatch, claims)

    response = _login(flask_app.test_client())

    assert response.status_code == 403
    assert "autorizada" in response.json["error"]


def test_invited_user_without_an_application_role_is_denied(
    monkeypatch,
):
    claims = _claims(role=None)
    flask_app = _create_app(monkeypatch, claims)

    response = _login(flask_app.test_client())

    assert response.status_code == 403
    assert "permiso" in response.json["error"]


def test_non_admin_cannot_open_admin_panel(monkeypatch):
    flask_app = _create_app(monkeypatch, _claims())
    client = flask_app.test_client()

    _login(client)
    response = client.get("/admin")

    assert response.status_code == 403


def test_admin_can_load_panel_and_user_list(monkeypatch):
    claims = _claims(
        email="admin@example.com",
        role="admin",
    )
    flask_app = _create_app(monkeypatch, claims)
    client = flask_app.test_client()
    _login(client)
    monkeypatch.setattr(
        auth,
        "_supabase_request",
        lambda settings, path, **kwargs: {
            "users": [
                {
                    "id": "user-id",
                    "email": "user@example.com",
                    "created_at": "2026-01-01T00:00:00Z",
                    "last_sign_in_at": None,
                    "app_metadata": {"role": "user"},
                },
            ],
        },
    )

    panel = client.get("/admin")
    users = client.get("/auth/admin/users")

    assert panel.status_code == 200
    assert b"Administraci" in panel.data
    assert users.status_code == 200
    assert users.json["users"][0]["last_sign_in_at"] is None


def test_admin_invite_sets_the_server_managed_user_role(monkeypatch):
    claims = _claims(email="admin@example.com", role="admin")
    flask_app = _create_app(monkeypatch, claims)
    client = flask_app.test_client()
    _login(client)
    calls = []

    def fake_request(settings, path, **kwargs):
        calls.append((path, kwargs))
        if path.startswith("/auth/v1/invite?"):
            return {"user": {"id": "invited-id"}}
        return {"user": {"id": "invited-id"}}

    monkeypatch.setattr(auth, "_supabase_request", fake_request)

    response = client.post(
        "/auth/admin/users",
        json={"email": "new-user@example.com"},
        headers={"Origin": "http://localhost:5000"},
    )

    assert response.status_code == 201
    assert len(calls) == 2
    assert calls[1][1]["body"] == {
        "app_metadata": {"role": "user"},
    }


def test_admin_sends_password_recovery_to_the_account_email(
    monkeypatch,
):
    claims = _claims(email="admin@example.com", role="admin")
    flask_app = _create_app(monkeypatch, claims)
    client = flask_app.test_client()
    _login(client)
    calls = []

    def fake_request(settings, path, **kwargs):
        calls.append((path, kwargs))
        if path == "/auth/v1/admin/users/user-id":
            return {"email": "user@example.com"}
        return {}

    monkeypatch.setattr(auth, "_supabase_request", fake_request)

    response = client.post(
        "/auth/admin/users/user-id/reset-password",
        headers={"Origin": "http://localhost:5000"},
    )

    assert response.status_code == 200
    assert calls[1][0].startswith("/auth/v1/recover?")
    assert calls[1][1]["body"] == {"email": "user@example.com"}
    assert calls[1][1].get("admin", False) is False


def test_admin_can_delete_a_regular_user(monkeypatch):
    claims = _claims(email="admin@example.com", role="admin")
    flask_app = _create_app(monkeypatch, claims)
    client = flask_app.test_client()
    _login(client)
    calls = []

    def fake_request(settings, path, **kwargs):
        calls.append((path, kwargs))
        if path.endswith("/admin/users/user-id"):
            return {
                "id": "user-id",
                "email": "user@example.com",
                "app_metadata": {"role": "user"},
            }
        return {}

    monkeypatch.setattr(auth, "_supabase_request", fake_request)

    response = client.delete(
        "/auth/admin/users/user-id",
        headers={"Origin": "http://localhost:5000"},
    )

    assert response.status_code == 200
    assert calls[-1][1]["admin"] is True
    assert calls[-1][1]["method"] == "DELETE"


def test_admin_cannot_delete_another_admin(monkeypatch):
    claims = _claims(email="admin@example.com", role="admin")
    flask_app = _create_app(monkeypatch, claims)
    client = flask_app.test_client()
    _login(client)
    calls = []

    def fake_request(settings, path, **kwargs):
        calls.append((path, kwargs))
        return {
            "id": "other-admin",
            "email": "other-admin@example.com",
            "app_metadata": {"role": "admin"},
        }

    monkeypatch.setattr(auth, "_supabase_request", fake_request)

    response = client.delete(
        "/auth/admin/users/other-admin",
        headers={"Origin": "http://localhost:5000"},
    )

    assert response.status_code == 409
    assert len(calls) == 1
