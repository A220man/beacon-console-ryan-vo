import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db_session
from app.models import User, UserRole, Skill, SkillCategory, SkillStatus
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine):
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_engine):
    """Create a test client with overridden database."""
    from httpx import AsyncClient, ASGITransport
    
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async def override_get_db_session():
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def authenticated_client(client, test_session: AsyncSession, test_user: User):
    """Create a client with authenticated session cookies."""
    from app.core.security import sign_session_data, generate_csrf_token, sign_csrf_token
    import json
    
    csrf_token = generate_csrf_token()
    session_data = {
        "user_id": test_user.id,
        "username": test_user.username,
        "role": test_user.role.value,
        "csrf_token": csrf_token,
    }
    signed_session = sign_session_data(json.dumps(session_data))
    signed_csrf = sign_csrf_token(csrf_token)

    client.cookies.set("session", signed_session)
    client.cookies.set("csrf_token", signed_csrf)
    return client


@pytest.fixture(scope="function")
async def operator_client(client, test_session: AsyncSession, test_user: User):
    """Create an operator client with authenticated session cookies."""
    from app.core.security import sign_session_data, generate_csrf_token, sign_csrf_token
    import json
    
    csrf_token = generate_csrf_token()
    session_data = {
        "user_id": test_user.id,
        "username": test_user.username,
        "role": test_user.role.value,
        "csrf_token": csrf_token,
    }
    signed_session = sign_session_data(json.dumps(session_data))
    signed_csrf = sign_csrf_token(csrf_token)

    client.cookies.set("session", signed_session)
    client.cookies.set("csrf_token", signed_csrf)
    return client


@pytest.fixture(scope="function")
async def user_client(client, test_session: AsyncSession, test_user: User):
    """Create a user client with authenticated session cookies."""
    from app.core.security import sign_session_data, generate_csrf_token, sign_csrf_token
    import json
    
    csrf_token = generate_csrf_token()
    session_data = {
        "user_id": test_user.id,
        "username": test_user.username,
        "role": test_user.role.value,
        "csrf_token": csrf_token,
    }
    signed_session = sign_session_data(json.dumps(session_data))
    signed_csrf = sign_csrf_token(csrf_token)

    client.cookies.set("session", signed_session)
    client.cookies.set("csrf_token", signed_csrf)
    return client


@pytest.fixture(scope="function")
async def test_user(test_session: AsyncSession) -> User:
    user = User(
        keycloak_sub="test-sub-123",
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        role=UserRole.OPERATOR,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def admin_user(test_session: AsyncSession) -> User:
    user = User(
        keycloak_sub="admin-sub-456",
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def test_skill(test_session: AsyncSession, test_user: User) -> Skill:
    skill = Skill(
        name="test-skill",
        display_name="Test Skill",
        description="A test skill for unit tests",
        category=SkillCategory.ANALYSIS,
        status=SkillStatus.VALIDATED,
        version="1.0.0",
        schema='{"type": "object", "properties": {"input": {"type": "string"}}}',
        metadata_json='{}',
        owner_id=test_user.id,
    )
    test_session.add(skill)
    await test_session.commit()
    await test_session.refresh(skill)
    return skill