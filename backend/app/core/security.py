import secrets
import time
from typing import Optional
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from app.core.config import get_settings

settings = get_settings()

_csrf_signer = TimestampSigner(settings.csrf_secret)
_session_signer = TimestampSigner(settings.secret_key)


def generate_csrf_token() -> str:
    """Generate a new CSRF token."""
    return secrets.token_urlsafe(32)


def sign_csrf_token(token: str) -> str:
    """Sign a CSRF token for cookie storage."""
    return _csrf_signer.sign(token.encode()).decode()


def verify_csrf_token(signed_token: str, max_age: int = 3600) -> Optional[str]:
    """Verify and return the raw CSRF token if valid."""
    try:
        return _csrf_signer.unsign(signed_token.encode(), max_age=max_age).decode()
    except (BadSignature, SignatureExpired):
        return None


def sign_session_data(data: str) -> str:
    """Sign session data for cookie storage."""
    return _session_signer.sign(data.encode()).decode()


def verify_session_data(signed_data: str, max_age: int = 604800) -> Optional[str]:
    """Verify and return session data if valid (default 7 days)."""
    try:
        return _session_signer.unsign(signed_data.encode(), max_age=max_age).decode()
    except (BadSignature, SignatureExpired):
        return None


def generate_state() -> str:
    """Generate a secure random state parameter for OAuth."""
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    """Generate a secure random nonce for OIDC."""
    return secrets.token_urlsafe(32)


def generate_pkce_verifier() -> str:
    """Generate a PKCE code verifier (43-128 chars)."""
    return secrets.token_urlsafe(96)[:128]


def pkce_challenge(verifier: str) -> str:
    """Generate PKCE code challenge (S256)."""
    import hashlib
    import base64
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def verify_pkce(verifier: str, challenge: str) -> bool:
    """Verify PKCE challenge matches verifier."""
    return secrets.compare_digest(pkce_challenge(verifier), challenge)