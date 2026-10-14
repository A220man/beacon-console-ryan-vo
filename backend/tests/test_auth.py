import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, UserRole
from app.core.security import sign_session_data, generate_csrf_token, sign_csrf_token
import json


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "beacon-console"

    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_authenticated(self, authenticated_client: AsyncClient, test_user: User):
        response = await authenticated_client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["role"] == test_user.role.value

    @pytest.mark.asyncio
    async def test_csrf_endpoint(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/api/auth/csrf")
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) > 0
    @pytest.mark.asyncio
    async def test_logout(self, authenticated_client: AsyncClient):
        from unittest.mock import AsyncMock, patch
        with patch("app.api.auth.get_oidc_config", new_callable=AsyncMock) as mock_get_oidc:
            mock_get_oidc.return_value = {
                "end_session_endpoint": "http://keycloak/realms/beacon/protocol/openid-connect/logout"
            }
            response = await authenticated_client.post("/api/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert "logout_url" in data


class TestAuthDependencies:
    @pytest.mark.asyncio
    async def test_require_auth_rejects_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/skills")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_require_role_allows_operator(self, operator_client: AsyncClient):
        response = await operator_client.post("/api/skills", json={
            "name": "test-skill",
            "display_name": "Test Skill",
            "description": "A test skill",
            "schema": {"type": "object"}
        })
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_require_role_denies_viewer(self, test_session: AsyncSession, client: AsyncClient):
        viewer = User(
            keycloak_sub="viewer-sub",
            email="viewer@test.com",
            username="viewer",
            role=UserRole.VIEWER,
        )
        test_session.add(viewer)
        await test_session.commit()
        await test_session.refresh(viewer)

        csrf_token = generate_csrf_token()
        session_data = {
            "user_id": viewer.id,
            "username": viewer.username,
            "role": viewer.role.value,
            "csrf_token": csrf_token,
        }
        signed_session = sign_session_data(json.dumps(session_data))
        signed_csrf = sign_csrf_token(csrf_token)
        client.cookies.set("session", signed_session)
        client.cookies.set("csrf_token", signed_csrf)

        response = await client.post("/api/skills", json={
            "name": "test-skill-2",
            "display_name": "Test Skill 2",
            "description": "A test skill",
            "schema": {"type": "object"}
        })
        assert response.status_code == 403