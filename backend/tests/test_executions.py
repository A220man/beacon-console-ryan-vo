import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, UserRole, Skill, SkillCategory, SkillStatus, Execution, ExecutionStatus
import json


@pytest.fixture
async def test_execution(test_session: AsyncSession, test_user: User, test_skill: Skill) -> Execution:
    execution = Execution(
        skill_id=test_skill.id,
        user_id=test_user.id,
        status=ExecutionStatus.PENDING,
        input_params='{"chromosome": "1", "start": 1000, "end": 2000}',
    )
    test_session.add(execution)
    await test_session.commit()
    await test_session.refresh(execution)
    return execution


class TestExecutionsEndpoints:
    @pytest.mark.asyncio
    async def test_list_executions_empty(self, user_client: AsyncClient):
        response = await user_client.get("/api/executions")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_execution(self, user_client: AsyncClient, test_skill: Skill):
        response = await user_client.post("/api/executions", json={
            "skill_id": test_skill.id,
            "input_params": {"chromosome": "1", "start": 1000, "end": 2000}
        })
        assert response.status_code == 201
        data = response.json()
        assert data["skill_id"] == test_skill.id
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_execution_invalid_skill(self, user_client: AsyncClient):
        response = await user_client.post("/api/executions", json={
            "skill_id": 99999,
            "input_params": {}
        })
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_execution(self, user_client: AsyncClient, test_execution: Execution):
        response = await user_client.get(f"/api/executions/{test_execution.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_execution.id
        assert data["skill_id"] == test_execution.skill_id
        assert "input_params" in data

    @pytest.mark.asyncio
    async def test_get_execution_not_found(self, user_client: AsyncClient):
        response = await user_client.get("/api/executions/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_run_execution(self, user_client: AsyncClient, test_execution: Execution):
        response = await user_client.post(f"/api/executions/{test_execution.id}/run")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_execution.id
        assert data["status"] in ("completed", "failed")
        if data["status"] == "completed":
            assert data["output_result"] is not None

    @pytest.mark.asyncio
    async def test_run_execution_twice(self, user_client: AsyncClient, test_execution: Execution):
        await user_client.post(f"/api/executions/{test_execution.id}/run")
        response = await user_client.post(f"/api/executions/{test_execution.id}/run")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_executions_with_filters(self, user_client: AsyncClient, test_execution: Execution):
        response = await user_client.get("/api/executions?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_executions_pagination(self, user_client: AsyncClient, test_session: AsyncSession, test_user: User, test_skill: Skill):
        for i in range(5):
            exec = Execution(
                skill_id=test_skill.id,
                user_id=test_user.id,
                status=ExecutionStatus.PENDING,
                input_params='{}',
            )
            test_session.add(exec)
        await test_session.commit()

        response = await user_client.get("/api/executions?page=1&page_size=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] >= 5


class TestDeterministicExecution:
    @pytest.mark.asyncio
    async def test_locus_compare_deterministic(self, test_session: AsyncSession, test_user: User):
        skill = Skill(
            name="locus-compare",
            display_name="Locus Compare",
            description="Generate locus compare plots",
            category=SkillCategory.GENETICS,
            status=SkillStatus.VALIDATED,
            schema='{"type": "object", "properties": {"chromosome": {"type": "string"}, "start": {"type": "integer"}, "end": {"type": "integer"}, "sentinel_snp": {"type": "string"}, "population": {"type": "string"}}, "required": ["chromosome", "start", "end", "sentinel_snp", "population"]}',
            owner_id=test_user.id,
        )
        test_session.add(skill)
        await test_session.commit()
        await test_session.refresh(skill)

        execution = Execution(
            skill_id=skill.id,
            user_id=test_user.id,
            status=ExecutionStatus.PENDING,
            input_params='{"chromosome": "1", "start": 1000, "end": 2000, "sentinel_snp": "rs123", "population": "EUR"}',
        )
        test_session.add(execution)
        await test_session.commit()
        await test_session.refresh(execution)

        from app.api.executions import run_skill_deterministic
        result = await run_skill_deterministic(skill, json.loads(execution.input_params))

        assert result["status"] == "completed"
        assert result["workflow"] == "locus-compare"
        assert "steps" in result
        assert result["steps"]["gwas_fetch"]["status"] == "completed"
        assert result["steps"]["eqtl_fetch"]["status"] == "completed"
        assert result["steps"]["ld_compute"]["status"] == "completed"
        assert result["steps"]["render"]["status"] == "completed"
        assert result["steps"]["render"]["panels"] == 4

    @pytest.mark.asyncio
    async def test_field_onboarding_deterministic(self, test_session: AsyncSession, test_user: User):
        skill = Skill(
            name="field-onboarding",
            display_name="Field Onboarding",
            description="Guided onboarding into unfamiliar research fields",
            category=SkillCategory.ONBOARDING,
            status=SkillStatus.VALIDATED,
            schema='{"type": "object", "properties": {"topic": {"type": "string"}, "mode": {"type": "string", "enum": ["onboard", "decode"]}}, "required": ["topic"]}',
            owner_id=test_user.id,
        )
        test_session.add(skill)
        await test_session.commit()
        await test_session.refresh(skill)

        execution = Execution(
            skill_id=skill.id,
            user_id=test_user.id,
            status=ExecutionStatus.PENDING,
            input_params='{"topic": "statistical genetics", "mode": "onboard"}',
        )
        test_session.add(execution)
        await test_session.commit()
        await test_session.refresh(execution)

        from app.api.executions import run_skill_deterministic
        result = await run_skill_deterministic(skill, json.loads(execution.input_params))

        assert result["status"] == "completed"
        assert result["workflow"] == "field-onboarding"
        assert result["topic"] == "statistical genetics"
        assert result["mode"] == "onboard"
        assert "steps" in result
        assert "prerequisites" in result["steps"]
        assert "ladder" in result["steps"]
        assert len(result["steps"]["ladder"]) == 5