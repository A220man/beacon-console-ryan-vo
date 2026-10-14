import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, UserRole, Skill, SkillCategory, SkillStatus, Execution, ExecutionStatus, AuditLog


class TestModels:
    @pytest.mark.asyncio
    async def test_user_creation(self, test_session: AsyncSession):
        user = User(
            keycloak_sub="test-sub",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.OPERATOR,
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        assert user.id is not None
        assert user.keycloak_sub == "test-sub"
        assert user.role == UserRole.OPERATOR
        assert user.is_active is True
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_user_role_enum(self):
        assert UserRole.VIEWER.value == "viewer"
        assert UserRole.OPERATOR.value == "operator"
        assert UserRole.ADMIN.value == "admin"

    @pytest.mark.asyncio
    async def test_skill_creation(self, test_session: AsyncSession, test_user: User):
        skill = Skill(
            name="test-skill",
            display_name="Test Skill",
            description="A test skill",
            category=SkillCategory.GENETICS,
            status=SkillStatus.VALIDATED,
            version="1.0.0",
            schema='{"type": "object"}',
            owner_id=test_user.id,
        )
        test_session.add(skill)
        await test_session.commit()
        await test_session.refresh(skill)

        assert skill.id is not None
        assert skill.category == SkillCategory.GENETICS
        assert skill.status == SkillStatus.VALIDATED

    @pytest.mark.asyncio
    async def test_skill_category_enum(self):
        assert SkillCategory.GENETICS.value == "genetics"
        assert SkillCategory.ONBOARDING.value == "onboarding"
        assert SkillCategory.OTHER.value == "other"

    @pytest.mark.asyncio
    async def test_skill_status_enum(self):
        assert SkillStatus.DRAFT.value == "draft"
        assert SkillStatus.VALIDATED.value == "validated"
        assert SkillStatus.DEPRECATED.value == "deprecated"

    @pytest.mark.asyncio
    async def test_execution_creation(self, test_session: AsyncSession, test_user: User, test_skill: Skill):
        execution = Execution(
            skill_id=test_skill.id,
            user_id=test_user.id,
            status=ExecutionStatus.PENDING,
            input_params='{"param": "value"}',
        )
        test_session.add(execution)
        await test_session.commit()
        await test_session.refresh(execution)

        assert execution.id is not None
        assert execution.status == ExecutionStatus.PENDING
        assert execution.input_params == '{"param": "value"}'

    @pytest.mark.asyncio
    async def test_execution_status_enum(self):
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.COMPLETED.value == "completed"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.CANCELLED.value == "cancelled"

    @pytest.mark.asyncio
    async def test_audit_log_creation(self, test_session: AsyncSession, test_user: User):
        audit = AuditLog(
            user_id=test_user.id,
            action="create",
            resource_type="skill",
            resource_id="1",
            details='{"name": "test"}',
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )
        test_session.add(audit)
        await test_session.commit()
        await test_session.refresh(audit)

        assert audit.id is not None
        assert audit.action == "create"
        assert audit.resource_type == "skill"
        assert audit.created_at is not None

    @pytest.mark.asyncio
    async def test_relationships(self, test_session: AsyncSession, test_user: User, test_skill: Skill):
        execution = Execution(
            skill_id=test_skill.id,
            user_id=test_user.id,
            status=ExecutionStatus.PENDING,
            input_params='{}',
        )
        test_session.add(execution)
        await test_session.commit()

        await test_session.refresh(test_user, attribute_names=["skills", "executions"])
        await test_session.refresh(test_skill, attribute_names=["executions"])

        assert len(test_user.skills) == 1
        assert test_user.skills[0].id == test_skill.id
        assert len(test_user.executions) == 1
        assert len(test_skill.executions) == 1