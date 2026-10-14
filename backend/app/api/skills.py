from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional
import json

from app.core.database import get_db_session
from app.api.auth import require_auth, require_role, UserRole
from app.models import Skill, SkillCategory, SkillStatus, User, Execution, ExecutionStatus, AuditLog

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("")
async def list_skills(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_auth),
    category: Optional[SkillCategory] = None,
    status: Optional[SkillStatus] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List skills with pagination and filtering."""
    query = select(Skill).options(selectinload(Skill.owner))

    if category:
        query = query.where(Skill.category == category)
    if status:
        query = query.where(Skill.status == status)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Skill.name.ilike(search_term),
                Skill.display_name.ilike(search_term),
                Skill.description.ilike(search_term),
            )
        )

    total_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    query = query.order_by(Skill.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    skills = result.scalars().all()

    return {
        "items": [
            {
                "id": s.id,
                "name": s.name,
                "display_name": s.display_name,
                "description": s.description,
                "category": s.category.value,
                "status": s.status.value,
                "version": s.version,
                "owner": {"id": s.owner.id, "username": s.owner.username},
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in skills
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{skill_id}")
async def get_skill(
    skill_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_auth),
) -> dict:
    """Get skill detail with schema."""
    result = await session.execute(
        select(Skill).options(selectinload(Skill.owner)).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    return {
        "id": skill.id,
        "name": skill.name,
        "display_name": skill.display_name,
        "description": skill.description,
        "category": skill.category.value,
        "status": skill.status.value,
        "version": skill.version,
        "schema": json.loads(skill.schema),
        "metadata": json.loads(skill.metadata_json),
        "owner": {"id": skill.owner.id, "username": skill.owner.username},
        "created_at": skill.created_at.isoformat(),
        "updated_at": skill.updated_at.isoformat(),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: dict,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_role([UserRole.OPERATOR, UserRole.ADMIN])),
) -> dict:
    """Create a new skill (operator/admin only)."""
    required_fields = ["name", "display_name", "description", "schema"]
    for field in required_fields:
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    existing = await session.execute(select(Skill).where(Skill.name == payload["name"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Skill name already exists")

    skill = Skill(
        name=payload["name"],
        display_name=payload["display_name"],
        description=payload["description"],
        category=SkillCategory(payload.get("category", "other")),
        status=SkillStatus(payload.get("status", "draft")),
        version=payload.get("version", "1.0.0"),
        schema=json.dumps(payload["schema"]),
        metadata_json=json.dumps(payload.get("metadata", {})),
        owner_id=user.id,
    )
    session.add(skill)
    await session.flush()

    audit = AuditLog(
        user_id=user.id,
        action="create",
        resource_type="skill",
        resource_id=str(skill.id),
        details=json.dumps({"name": skill.name}),
    )
    session.add(audit)

    return {
        "id": skill.id,
        "name": skill.name,
        "display_name": skill.display_name,
        "category": skill.category.value,
        "status": skill.status.value,
        "version": skill.version,
    }


@router.patch("/{skill_id}")
async def update_skill(
    skill_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_role([UserRole.OPERATOR, UserRole.ADMIN])),
) -> dict:
    """Update a skill (operator/admin only)."""
    result = await session.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    if "name" in payload and payload["name"] != skill.name:
        existing = await session.execute(select(Skill).where(Skill.name == payload["name"]))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Skill name already exists")
        skill.name = payload["name"]

    updatable = ["display_name", "description", "category", "status", "version", "schema", "metadata"]
    for field in updatable:
        if field in payload:
            if field in ("category", "status"):
                setattr(skill, field, SkillCategory(payload[field]) if field == "category" else SkillStatus(payload[field]))
            elif field in ("schema", "metadata"):
                setattr(skill, f"{field}_json" if field == "metadata" else field, json.dumps(payload[field]))
            else:
                setattr(skill, field, payload[field])

    audit = AuditLog(
        user_id=user.id,
        action="update",
        resource_type="skill",
        resource_id=str(skill.id),
        details=json.dumps(payload),
    )
    session.add(audit)

    return {
        "id": skill.id,
        "name": skill.name,
        "display_name": skill.display_name,
        "category": skill.category.value,
        "status": skill.status.value,
        "version": skill.version,
    }


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_role([UserRole.ADMIN])),
) -> None:
    """Delete a skill (admin only)."""
    result = await session.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    audit = AuditLog(
        user_id=user.id,
        action="delete",
        resource_type="skill",
        resource_id=str(skill.id),
        details=json.dumps({"name": skill.name}),
    )
    session.add(audit)

    await session.delete(skill)