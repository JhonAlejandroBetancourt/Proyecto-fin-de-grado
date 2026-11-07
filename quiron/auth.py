"""Autenticación y administración de cuentas mediante Supabase Auth."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

import jwt
from flask import (
    Blueprint,
    Flask,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
)


AUTH_COOKIE_NAME = "quiron_access"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_JWT_ALGORITHMS = ("ES256", "RS256", "EdDSA")


class AuthConfigurationError(RuntimeError):
    """Configuración incompleta o inválida del proveedor de identidad."""


class AuthenticationError(RuntimeError):
    """Token o identidad no autorizados para la aplicación."""


class SupabaseAPIError(RuntimeError):
    """Error explícito devuelto por Supabase Auth."""


@dataclass(frozen=True)
class AuthSettings:
    enabled: bool
    supabase_url: str = ""
    anon_key: str = ""
    service_role_key: str = ""
    base_url: str = ""
    admin_emails: frozenset[str] = frozenset()
    google_allowed_emails: frozenset[str] = frozenset()


def _as_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _parse_emails(value: str) -> frozenset[str]:
    return frozenset(
        email.strip().lower()
        for email in value.split(",")
        if email.strip()
    )


def load_auth_settings() -> AuthSettings:
    configured_flag = os.getenv("QUIRON_AUTH_ENABLED")
    enabled = (
        True
        if _as_bool(os.getenv("VERCEL"))
        else _as_bool(configured_flag)
    )
    if not enabled:
        return AuthSettings(enabled=False)

    required = (
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "QUIRON_BASE_URL",
        "QUIRON_ADMIN_EMAILS",
    )
    missing = [
        key
        for key in required
        if not os.getenv(key, "").strip()
    ]
    if missing:
        raise AuthConfigurationError(
            "La autenticación está activada, pero faltan variables "
            "requeridas: "
            + ", ".join(missing)
        )

    supabase_url = os.environ["SUPABASE_URL"].strip().rstrip("/")
    base_url = os.environ["QUIRON_BASE_URL"].strip().rstrip("/")
    supabase_parts = urlparse(supabase_url)
    if (
        supabase_parts.scheme != "https"
        or not supabase_parts.netloc
        or supabase_parts.username
        or supabase_parts.password
        or supabase_parts.path not in {"", "/"}
        or supabase_parts.query
        or supabase_parts.fragment
    ):
        raise AuthConfigurationError(
            "SUPABASE_URL debe ser un origen HTTPS válido."
        )
    base_parts = urlparse(base_url)
    local_http = (
        base_parts.scheme == "http"
        and base_parts.hostname in {"localhost", "127.0.0.1"}
    )
    if (
        (base_parts.scheme != "https" and not local_http)
        or not base_parts.netloc
        or base_parts.username
        or base_parts.password
        or base_parts.path not in {"", "/"}
        or base_parts.query
        or base_parts.fragment
    ):
        raise AuthConfigurationError(
            "QUIRON_BASE_URL debe ser un origen HTTPS válido "
            "(se permite localhost para desarrollo)."
        )

    admin_emails = _parse_emails(
        os.environ["QUIRON_ADMIN_EMAILS"]
    )
    google_allowed_emails = _parse_emails(
        os.getenv("QUIRON_GOOGLE_ALLOWED_EMAILS", "")
    )
    if not admin_emails or any(
        not _EMAIL_RE.fullmatch(email)
        for email in admin_emails | google_allowed_emails
    ):
        raise AuthConfigurationError(
            "Los correos de administración y Google deben ser "
            "direcciones válidas."
        )

    return AuthSettings(
        enabled=True,
        supabase_url=supabase_url,
        anon_key=os.environ["SUPABASE_ANON_KEY"].strip(),
        service_role_key=os.environ[
            "SUPABASE_SERVICE_ROLE_KEY"
        ].strip(),
        base_url=base_url,
        admin_emails=admin_emails,
        google_allowed_emails=google_allowed_emails,
    )


def _supabase_request(
    settings: AuthSettings,
    path: str,
    *,
    method: str = "GET",
    body: dict | None = None,
    admin: bool = False,
) -> dict:
    api_key = (
        settings.service_role_key
        if admin
        else settings.anon_key
    )
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(
        f"{settings.supabase_url}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(req, timeout=12) as response:
            response_body = response.read()
    except HTTPError as error:
        try:
            detail = json.loads(error.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            detail = {}
        message = (
            detail.get("msg")
            or detail.get("message")
            or detail.get("error_description")
            or detail.get("error")
            or "Error del proveedor de autenticación."
        )
        raise SupabaseAPIError(
            f"Supabase devolvió HTTP {error.code}: {message}"
        ) from error
    except (TimeoutError, URLError) as error:
        raise SupabaseAPIError(
            "No fue posible conectar con Supabase Auth."
        ) from error

    if not response_body:
        return {}
    try:
        result = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SupabaseAPIError(
            "Supabase devolvió una respuesta inválida."
        ) from error
    if not isinstance(result, dict):
        raise SupabaseAPIError(
            "Supabase devolvió una respuesta inesperada."
        )
    return result


def _verify_access_token(
    token: str,
    settings: AuthSettings,
    jwks_client: jwt.PyJWKClient,
) -> dict:
    if not token or len(token) > 16_384:
        raise AuthenticationError("Sesión no válida.")
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(
            token
        )
        if signing_key.algorithm_name not in _JWT_ALGORITHMS:
            raise AuthenticationError(
                "Algoritmo de firma no permitido."
            )
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[signing_key.algorithm_name],
            audience="authenticated",
            issuer=f"{settings.supabase_url}/auth/v1",
            options={
                "require": ["exp", "sub", "iss", "aud"],
            },
            leeway=30,
        )
    except AuthenticationError:
        raise
    except (jwt.PyJWTError, ValueError, URLError) as error:
        raise AuthenticationError(
            "La sesión no es válida o ha expirado."
        ) from error


def _claims_email(claims: dict) -> str:
    return str(claims.get("email", "")).strip().lower()


def _is_admin(
    claims: dict,
    settings: AuthSettings,
) -> bool:
    email = _claims_email(claims)
    app_metadata = claims.get("app_metadata") or {}
    return (
        email in settings.admin_emails
        or app_metadata.get("role") == "admin"
    )


def _authorize_claims(
    claims: dict,
    settings: AuthSettings,
) -> bool:
    email = _claims_email(claims)
    app_metadata = claims.get("app_metadata") or {}
    providers = app_metadata.get("providers") or []
    provider = app_metadata.get("provider")
    role = app_metadata.get("role")

    if not email:
        raise AuthenticationError(
            "La cuenta no tiene un correo verificado."
        )
    if claims.get("aal") != "aal2":
        raise AuthenticationError(
            "Se requiere completar la verificación MFA."
        )
    if (
        "google" in providers
        or provider == "google"
    ) and (
        email not in settings.google_allowed_emails
    ):
        raise AuthenticationError(
            "Esta cuenta de Google no está autorizada."
        )
    if (
        role not in {"user", "admin"}
        and email not in settings.admin_emails
    ):
        raise AuthenticationError(
            "La cuenta no tiene permiso para acceder a Quirón."
        )
    return _is_admin(claims, settings)


def _same_origin(settings: AuthSettings) -> bool:
    origin = request.headers.get("Origin", "").rstrip("/")
    return origin == settings.base_url


def _api_error(message: str, status: int):
    return jsonify({"error": message}), status


def _get_supabase_user(
    settings: AuthSettings,
    user_id: str,
) -> dict:
    result = _supabase_request(
        settings,
        f"/auth/v1/admin/users/{quote(user_id, safe='')}",
        admin=True,
    )
    return result.get("user", result)


def _account_role(
    user: dict,
    settings: AuthSettings,
) -> str:
    email = str(user.get("email", "")).strip().lower()
    app_metadata = user.get("app_metadata") or {}
    if (
        email in settings.admin_emails
        or app_metadata.get("role") == "admin"
    ):
        return "admin"
    return "user"


def register_auth(app: Flask) -> None:
    """Configura rutas y protección; en producción la falta de config falla."""

    settings = load_auth_settings()
    app.config["QUIRON_AUTH_ENABLED"] = settings.enabled
    if not settings.enabled:
        return

    app.config["SESSION_COOKIE_SECURE"] = (
        settings.base_url.startswith("https://")
    )
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    jwks_url = (
        f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    )
    jwks_client = jwt.PyJWKClient(jwks_url)
    app.extensions["quiron_auth_settings"] = settings
    app.extensions["quiron_auth_jwks"] = jwks_client
    app.extensions["quiron_auth_public_config"] = {
        "supabase_url": settings.supabase_url,
        "anon_key": settings.anon_key,
    }

    blueprint = Blueprint(
        "quiron_auth",
        __name__,
        template_folder="templates",
    )

    @app.before_request
    def proteger_aplicacion():
        path = request.path
        if (
            path in {
                "/login",
                "/auth/session",
                "/auth/logout",
            }
            or path.startswith("/assets/")
            or path == "/_favicon.ico"
        ):
            return None

        token = request.cookies.get(AUTH_COOKIE_NAME, "")
        if not token:
            return _respuesta_no_autorizada()
        try:
            claims = _verify_access_token(
                token,
                settings,
                jwks_client,
            )
            admin = _authorize_claims(claims, settings)
        except AuthenticationError:
            return _respuesta_no_autorizada()

        g.auth_claims = claims
        g.auth_is_admin = admin
        if path == "/admin" and not admin:
            return "Acceso reservado a administradores.", 403
        if path.startswith("/auth/admin/") and not admin:
            return _api_error(
                "Acceso reservado a administradores.",
                403,
            )
        return None

    def _respuesta_no_autorizada():
        if (
            request.path.startswith("/_dash-")
            or request.path.startswith("/auth/admin/")
            or request.path == "/auth/status"
        ):
            return _api_error(
                "La sesión expiró. Inicia sesión de nuevo.",
                401,
            )
        next_path = request.full_path
        if next_path.endswith("?"):
            next_path = request.path
        response = redirect(
            f"/login?{urlencode({'next': next_path})}"
        )
        response.delete_cookie(
            AUTH_COOKIE_NAME,
            path="/",
            secure=app.config["SESSION_COOKIE_SECURE"],
            httponly=True,
            samesite="Lax",
        )
        return response

    @blueprint.get("/login")
    def login_page():
        return render_template(
            "login.html",
            supabase_url=settings.supabase_url,
            supabase_anon_key=settings.anon_key,
            google_enabled=bool(
                settings.google_allowed_emails
            ),
        )

    @blueprint.post("/auth/session")
    def establish_session():
        if not _same_origin(settings):
            return _api_error("Origen no permitido.", 403)
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return _api_error(
                "La solicitud debe contener un objeto JSON.",
                400,
            )
        token = payload.get("access_token")
        if not isinstance(token, str):
            return _api_error(
                "Falta el token de acceso.",
                400,
            )
        try:
            claims = _verify_access_token(
                token,
                settings,
                jwks_client,
            )
            is_admin = _authorize_claims(
                claims,
                settings,
            )
        except AuthenticationError as error:
            return _api_error(str(error), 403)

        max_age = max(
            0,
            int(claims["exp"] - time.time()),
        )
        response = jsonify(
            {
                "email": _claims_email(claims),
                "is_admin": is_admin,
            }
        )
        response.set_cookie(
            AUTH_COOKIE_NAME,
            token,
            max_age=max_age,
            httponly=True,
            secure=app.config["SESSION_COOKIE_SECURE"],
            samesite="Lax",
            path="/",
        )
        return response

    @blueprint.route("/auth/logout", methods=["GET", "POST"])
    def logout():
        if request.method == "GET":
            return render_template(
                "logout.html",
                supabase_url=settings.supabase_url,
                supabase_anon_key=settings.anon_key,
            )
        if not _same_origin(settings):
            return _api_error("Origen no permitido.", 403)
        response = redirect("/login")
        response.delete_cookie(
            AUTH_COOKIE_NAME,
            path="/",
            secure=app.config["SESSION_COOKIE_SECURE"],
            httponly=True,
            samesite="Lax",
        )
        return response

    @blueprint.get("/admin")
    def admin_page():
        return render_template(
            "admin.html",
            supabase_url=settings.supabase_url,
            supabase_anon_key=settings.anon_key,
        )

    @blueprint.get("/auth/status")
    def auth_status():
        return jsonify(
            {
                "email": _claims_email(g.auth_claims),
                "is_admin": g.auth_is_admin,
            }
        )

    @blueprint.get("/auth/admin/users")
    def admin_list_users():
        users = []
        try:
            for page in range(1, 6):
                result = _supabase_request(
                    settings,
                    (
                        "/auth/v1/admin/users?"
                        + urlencode(
                            {
                                "page": page,
                                "per_page": 100,
                            }
                        )
                    ),
                    admin=True,
                )
                page_users = result.get("users", [])
                users.extend(
                    {
                        "id": user.get("id"),
                        "email": user.get("email"),
                        "created_at": user.get("created_at"),
                        "last_sign_in_at": user.get(
                            "last_sign_in_at"
                        ),
                        "role": _account_role(user, settings),
                    }
                    for user in page_users
                )
                if len(page_users) < 100:
                    break
        except SupabaseAPIError as error:
            app.logger.warning(
                "No fue posible consultar las cuentas de Quirón: %s",
                error,
            )
            return _api_error(str(error), 502)
        return jsonify({"users": users})

    @blueprint.post("/auth/admin/users")
    def admin_invite_user():
        if not _same_origin(settings):
            return _api_error("Origen no permitido.", 403)
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return _api_error(
                "La solicitud debe contener un objeto JSON.",
                400,
            )
        email = str(payload.get("email", "")).strip().lower()
        if not _EMAIL_RE.fullmatch(email):
            return _api_error(
                "Introduce una dirección de correo válida.",
                400,
            )
        try:
            invited = _supabase_request(
                settings,
                "/auth/v1/invite?"
                + urlencode(
                    {
                        "redirect_to": (
                            f"{settings.base_url}/login"
                        ),
                    }
                ),
                method="POST",
                body={"email": email},
                admin=True,
            )
            user = invited.get("user") or invited
            user_id = user.get("id")
            if not user_id:
                raise SupabaseAPIError(
                    "Supabase no devolvió el identificador de cuenta."
                )
            _supabase_request(
                settings,
                (
                    "/auth/v1/admin/users/"
                    f"{quote(str(user_id), safe='')}"
                ),
                method="PUT",
                body={
                    "app_metadata": {
                        "role": "user",
                    },
                },
                admin=True,
            )
        except SupabaseAPIError as error:
            app.logger.warning(
                "No fue posible invitar una cuenta de Quirón: %s",
                error,
            )
            return _api_error(str(error), 502)
        return jsonify(
            {
                "message": (
                    f"Se envió una invitación a {email}."
                ),
            }
        ), 201

    @blueprint.post(
        "/auth/admin/users/<user_id>/reset-password"
    )
    def admin_reset_password(user_id: str):
        if not _same_origin(settings):
            return _api_error("Origen no permitido.", 403)
        try:
            user = _get_supabase_user(settings, user_id)
            email = str(user.get("email", "")).strip().lower()
            if not email:
                return _api_error(
                    "La cuenta solicitada no existe.",
                    404,
                )
            _supabase_request(
                settings,
                "/auth/v1/recover?"
                + urlencode(
                    {
                        "redirect_to": (
                            f"{settings.base_url}/login"
                        ),
                    }
                ),
                method="POST",
                body={"email": email},
            )
        except SupabaseAPIError as error:
            app.logger.warning(
                "No fue posible enviar recuperación de contraseña: %s",
                error,
            )
            return _api_error(str(error), 502)
        return jsonify(
            {
                "message": (
                    f"Se envió el enlace de recuperación a {email}."
                ),
            }
        )

    @blueprint.delete("/auth/admin/users/<user_id>")
    def admin_delete_user(user_id: str):
        if not _same_origin(settings):
            return _api_error("Origen no permitido.", 403)
        try:
            user = _get_supabase_user(settings, user_id)
            email = str(user.get("email", "")).strip().lower()
            app_metadata = user.get("app_metadata") or {}
            if not email:
                return _api_error(
                    "La cuenta solicitada no existe.",
                    404,
                )
            if (
                email in settings.admin_emails
                or app_metadata.get("role") == "admin"
            ):
                return _api_error(
                    "No se permite eliminar una cuenta administradora.",
                    409,
                )
            _supabase_request(
                settings,
                (
                    "/auth/v1/admin/users/"
                    f"{quote(user_id, safe='')}"
                ),
                method="DELETE",
                admin=True,
            )
        except SupabaseAPIError as error:
            app.logger.warning(
                "No fue posible eliminar una cuenta de Quirón: %s",
                error,
            )
            return _api_error(str(error), 502)
        return jsonify({"message": "Cuenta eliminada."})

    app.register_blueprint(blueprint)

    @app.after_request
    def agregar_cabeceras_seguridad(response):
        response.headers.setdefault(
            "X-Content-Type-Options",
            "nosniff",
        )
        response.headers.setdefault(
            "X-Frame-Options",
            "DENY",
        )
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        if not request.path.startswith(
            ("/assets/", "/_dash-component-suites/")
        ):
            response.headers["Cache-Control"] = "no-store"
        return response
