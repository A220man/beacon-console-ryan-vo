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
        assert len(result["steps"]["ladder"]) == 5


class TestLLMExplanation:
    @pytest.mark.asyncio
    async def test_explain_execution_no_llm_key(self, user_client: AsyncClient, test_execution: Execution):
        """Test explanation endpoint when LLM_API_KEY is not configured."""
        # First run the execution to completion
        await user_client.post(f"/api/executions/{test_execution.id}/run")
        response = await user_client.post(f"/api/executions/{test_execution.id}/explain")

        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == test_execution.id
        assert "explanation" in data
        assert data["explanation"]["status"] == "skipped"
        assert data["explanation"]["reason"] == "LLM_API_KEY not configured"
        assert data["explanation"]["advisory"] is True

    @pytest.mark.asyncio
    async def test_explain_execution_not_completed(self, user_client: AsyncClient, test_execution: Execution):
        """Test explanation endpoint rejects non-completed executions."""
        response = await user_client.post(f"/api/executions/{test_execution.id}/explain")
        assert response.status_code == 400
        assert "completed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_explain_execution_not_found(self, user_client: AsyncClient):
        """Test explanation endpoint returns 404 for non-existent execution."""
        response = await user_client.post("/api/executions/99999/explain")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_explain_execution_requires_auth(self, client: AsyncClient, test_execution: Execution):
        """Test explanation endpoint requires authentication."""
        # Run to completion as test_user (owner)
        from app.core.security import sign_session_data, generate_csrf_token, sign_csrf_token
        import json
        from app.models import User, UserRole
        from sqlalchemy.ext.asyncio import AsyncSession
        # First need to run as authenticated user
        # This test just verifies unauthenticated request fails
        response = await client.post(f"/api/executions/{test_execution.id}/explain")
        assert response.status_code in (401, 403)
    @pytest.mark.asyncio
    async def test_generate_explanation_no_api_key(self):
        """Test generate_explanation returns skipped when no API key."""
        from app.core.config import Settings
        from app.services.llm import generate_explanation

        class MockSettings:
            llm_api_key = ""
            llm_provider = "openai-compatible"
            llm_model = "gpt-4o-mini"
            llm_base_url = "https://api.openai.com/v1"
            llm_timeout_seconds = 30

        result = await generate_explanation(
            skill_name="locus-compare",
            skill_display_name="Locus Compare",
            input_params={"chromosome": "1", "start": 1000, "end": 2000, "sentinel_snp": "rs123", "population": "EUR"},
            deterministic_result={"status": "completed", "workflow": "locus-compare"},
            settings=MockSettings(),
        )

        assert result["status"] == "skipped"
        assert result["reason"] == "LLM_API_KEY not configured"
        assert result["advisory"] is True

    @pytest.mark.asyncio
    async def test_get_llm_provider_factory(self):
        """Test get_llm_provider factory returns correct provider types."""
        from app.services.llm import get_llm_provider, OpenAICompatibleProvider, AnthropicProvider, GeminiProvider

        openai_provider = get_llm_provider("openai-compatible", "test-key", "https://api.openai.com/v1", "gpt-4o-mini")
        assert isinstance(openai_provider, OpenAICompatibleProvider)

        anthropic_provider = get_llm_provider("anthropic", "test-key", "https://api.anthropic.com", "claude-3-haiku")
        assert isinstance(anthropic_provider, AnthropicProvider)

        gemini_provider = get_llm_provider("gemini", "test-key", "https://generativelanguage.googleapis.com", "gemini-1.5-flash")
        assert isinstance(gemini_provider, GeminiProvider)

        ollama_provider = get_llm_provider("ollama", "test-key", "http://localhost:11434/v1", "llama3")
        assert isinstance(ollama_provider, OpenAICompatibleProvider)

    @pytest.mark.asyncio
    async def test_get_llm_provider_unknown(self):
        """Test get_llm_provider raises for unknown provider."""
        from app.services.llm import get_llm_provider
        import pytest

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_provider("unknown", "test-key", "https://example.com", "model")