import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, UserRole, Skill, SkillCategory, SkillStatus
import json


class TestSkillsEndpoints:
    @pytest.mark.asyncio
    async def test_list_skills_empty(self, operator_client: AsyncClient):
        response = await operator_client.get("/api/skills")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_skill(self, operator_client: AsyncClient, test_user: User):
        response = await operator_client.post("/api/skills", json={
            "name": "locus-compare",
            "display_name": "Locus Compare",
            "description": "Generate locus compare plots for statistical genetics",
            "category": "genetics",
            "status": "validated",
            "version": "1.0.0",
            "schema": {
                "type": "object",
                "properties": {
                    "chromosome": {"type": "string"},
                    "start": {"type": "integer"},
                    "end": {"type": "integer"},
                    "sentinel_snp": {"type": "string"},
                    "population": {"type": "string"}
                },
                "required": ["chromosome", "start", "end", "sentinel_snp", "population"]
            },
            "metadata": {"source": "upstream"}
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "locus-compare"
        assert data["category"] == "genetics"
        assert data["status"] == "validated"

    @pytest.mark.asyncio
    async def test_create_skill_duplicate_name(self, operator_client: AsyncClient, test_skill: Skill):
        response = await operator_client.post("/api/skills", json={
            "name": test_skill.name,
            "display_name": "Another Skill",
            "description": "Duplicate",
            "schema": {"type": "object"}
        })
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_skill(self, operator_client: AsyncClient, test_skill: Skill):
        response = await operator_client.get(f"/api/skills/{test_skill.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_skill.id
        assert data["name"] == test_skill.name
        assert "schema" in data
        assert "metadata" in data

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, operator_client: AsyncClient):
        response = await operator_client.get("/api/skills/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_skill(self, operator_client: AsyncClient, test_skill: Skill):
        response = await operator_client.patch(f"/api/skills/{test_skill.id}", json={
            "display_name": "Updated Name",
            "status": "deprecated"
        })
        assert response.status_code == 200
        data = response.json()
    @pytest.mark.asyncio
    async def test_list_skills_with_filters(self, operator_client: AsyncClient, test_skill: Skill):
        response = await operator_client.get("/api/skills?category=analysis&status=validated")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["category"] == "analysis"

    @pytest.mark.asyncio
    async def test_list_skills_search(self, operator_client: AsyncClient, test_skill: Skill):
        response = await operator_client.get("/api/skills?search=test")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_skills_pagination(self, operator_client: AsyncClient, test_session: AsyncSession, test_user: User):
        for i in range(5):
            skill = Skill(
                name=f"skill-{i}",
                display_name=f"Skill {i}",
                description=f"Description {i}",
                category=SkillCategory.ANALYSIS,
                status=SkillStatus.VALIDATED,
                schema='{"type": "object"}',
                owner_id=test_user.id,
            )
            test_session.add(skill)
        await test_session.commit()

        response = await operator_client.get("/api/skills?page=1&page_size=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] >= 5
        assert data["page"] == 1
        assert data["page_size"] == 3