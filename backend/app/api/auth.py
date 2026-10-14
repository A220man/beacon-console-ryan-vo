from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from urllib.parse import urlencode
import httpx
import json

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.security import (
    generate_state,
    generate_nonce,
    generate_pkce_verifier,
    pkce_challenge,
    sign_session_data,
    verify_session_data,
    sign_csrf_token,
    generate_csrf_token,
)
from app.models import User, UserRole, AuditLog

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

OIDC_DISCOVERY_CACHE: dict = {}


async def get_oidc_config() -> dict:
    """Fetch and cache OIDC discovery document."""
    if "config" not in OIDC_DISCOVERY_CACHE:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(settings.oidc_discovery_url)
            resp.raise_for_status()
            OIDC_DISCOVERY_CACHE["config"] = resp.json()
    return OIDC_DISCOVERY_CACHE["config"]


def set_auth_cookies(response: Response, session_data: dict, csrf_token: str) -> None:
    """Set authentication cookies."""
    signed_session = sign_session_data(json.dumps(session_data))
    signed_csrf = sign_csrf_token(csrf_token)

    cookie_kwargs = {
        "httponly": True,
        "secure": settings.is_production,
        "samesite": "lax",
        "path": "/",
    }

    response.set_cookie("session", signed_session, max_age=604800, **cookie_kwargs)
    response.set_cookie("csrf_token", signed_csrf, max_age=3600, **cookie_kwargs)


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies."""
    cookie_kwargs = {
        "httponly": True,
        "secure": settings.is_production,
        "samesite": "lax",
        "path": "/",
    }
    response.delete_cookie("session", **cookie_kwargs)
    response.delete_cookie("csrf_token", **cookie_kwargs)


def get_session_data(request: Request) -> dict | None:
    """Extract and verify session from cookie."""
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return None
    data = verify_session_data(session_cookie, max_age=604800)
    if not data:
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def get_current_user_id(request: Request) -> int | None:
    """Get current user ID from session."""
    session = get_session_data(request)
    if not session:
        return None
    return session.get("user_id")


async def require_auth(request: Request, session: AsyncSession = Depends(get_db_session)) -> User:
    """Dependency to require authenticated user."""
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_role(allowed_roles: list[UserRole]):
    """Dependency factory for role-based access."""
    async def check_role(user: User = Depends(require_auth)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return check_role


@router.get("/login")
async def login(request: Request, response: Response) -> RedirectResponse:
    """Initiate OIDC login flow with PKCE."""
    oidc_config = await get_oidc_config()
    auth_endpoint = oidc_config["authorization_endpoint"]

    state = generate_state()
    nonce = generate_nonce()
    pkce_verifier = generate_pkce_verifier()
    pkce_challenge_value = pkce_challenge(pkce_verifier)

    csrf_token = generate_csrf_token()

    session_data = {
        "oauth_state": state,
        "oauth_nonce": nonce,
        "pkce_verifier": pkce_verifier,
        "csrf_token": csrf_token,
    }

    set_auth_cookies(response, session_data, csrf_token)

    params = {
        "client_id": settings.oidc_client_id,
        "redirect_uri": settings.oidc_redirect_uri,
        "response_type": "code",
        "scope": settings.oidc_scopes,
        "state": state,
        "nonce": nonce,
        "code_challenge": pkce_challenge_value,
        "code_challenge_method": "S256",
    }

    auth_url = f"{auth_endpoint}?{urlencode(params)}"
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/callback")
async def callback(
    request: Request,
    response: Response,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    """Handle OIDC callback and exchange code for tokens."""
    if error:
        clear_auth_cookies(response)
        raise HTTPException(status_code=400, detail=f"OIDC error: {error} - {error_description}")

    session_data = get_session_data(request)
    if not session_data:
        clear_auth_cookies(response)
        raise HTTPException(status_code=400, detail="Invalid or expired session")

    expected_state = session_data.get("oauth_state")
    if not expected_state or state != expected_state:
        clear_auth_cookies(response)
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    pkce_verifier = session_data.get("pkce_verifier")
    if not pkce_verifier:
        clear_auth_cookies(response)
        raise HTTPException(status_code=400, detail="Missing PKCE verifier")

    oidc_config = await get_oidc_config()
    token_endpoint = oidc_config["token_endpoint"]

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.oidc_redirect_uri,
        "client_id": settings.oidc_client_id,
        "code_verifier": pkce_verifier,
    }
    if settings.oidc_client_secret:
        token_data["client_secret"] = settings.oidc_client_secret

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(token_endpoint, data=token_data)
        token_resp.raise_for_status()
        tokens = token_resp.json()

    id_token = tokens.get("id_token")
    access_token = tokens.get("access_token")

    if not id_token:
        clear_auth_cookies(response)
        raise HTTPException(status_code=400, detail="No ID token received")

    from jose import jwt
    jwks_uri = oidc_config["jwks_uri"]
    async with httpx.AsyncClient(timeout=10.0) as client:
        jwks_resp = await client.get(jwks_uri)
        jwks_resp.raise_for_status()
        jwks = jwks_resp.json()

    try:
        header = jwt.get_unverified_header(id_token)
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            raise ValueError("Matching JWK not found")

        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=settings.oidc_client_id,
            issuer=settings.oidc_issuer_url,
            options={"verify_at_hash": False},
        )
    except Exception as e:
        clear_auth_cookies(response)
        raise HTTPException(status_code=400, detail=f"Token validation failed: {str(e)}")

    if claims.get("nonce") != session_data.get("oauth_nonce"):
        clear_auth_cookies(response)
        raise HTTPException(status_code=400, detail="Nonce mismatch")

    sub = claims.get("sub")
    email = claims.get("email")
    username = claims.get("preferred_username", email)
    full_name = claims.get("name")

    result = await session.execute(select(User).where(User.keycloak_sub == sub))
    user = result.scalar_one_or_none()

    if user:
        user.email = email
        user.username = username
        user.full_name = full_name
        user.last_login_at = datetime.now(timezone.utc)
    else:
        user = User(
            keycloak_sub=sub,
            email=email,
            username=username,
            full_name=full_name,
            role=UserRole.VIEWER,
        )
        session.add(user)
        await session.flush()

    audit = AuditLog(
        user_id=user.id,
        action="login",
        resource_type="user",
        resource_id=str(user.id),
        details=json.dumps({"provider": "keycloak"}),
    )
    session.add(audit)

    new_csrf = generate_csrf_token()
    new_session_data = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value,
        "csrf_token": new_csrf,
    }
    set_auth_cookies(response, new_session_data, new_csrf)

    return RedirectResponse(url="/", status_code=302)


@router.post("/logout")
async def logout(request: Request, response: Response, session: AsyncSession = Depends(get_db_session)) -> dict:
    """Log out user and redirect to Keycloak logout."""
    user_id = get_current_user_id(request)
    if user_id:
        audit = AuditLog(
            user_id=user_id,
            action="logout",
            resource_type="user",
            resource_id=str(user_id),
            details=json.dumps({}),
        )
        session.add(audit)

    clear_auth_cookies(response)

    oidc_config = await get_oidc_config()
    logout_endpoint = oidc_config.get("end_session_endpoint")
    if logout_endpoint:
        params = {"post_logout_redirect_uri": settings.oidc_logout_redirect_uri}
        logout_url = f"{logout_endpoint}?{urlencode(params)}"
        return {"logout_url": logout_url}

    return {"logout_url": settings.oidc_logout_redirect_uri}


@router.get("/me")
async def get_current_user(user: User = Depends(require_auth)) -> dict:
    """Get current authenticated user info."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
    }


@router.get("/csrf")
async def get_csrf_token(request: Request, response: Response) -> dict:
    """Get a fresh CSRF token for forms."""
    session_data = get_session_data(request)
    if not session_data:
        raise HTTPException(status_code=401, detail="Not authenticated")

    csrf_token = generate_csrf_token()
    session_data["csrf_token"] = csrf_token
    set_auth_cookies(response, session_data, csrf_token)
    return {"csrf_token": csrf_token}


from datetime import datetime, timezone