from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
import json
import uuid
from datetime import datetime, timezone

from app.core.database import get_db_session
from app.core.config import get_settings
from app.api.auth import require_auth, require_role, UserRole
from app.models import Skill, Execution, ExecutionStatus, User, AuditLog
from app.services import generate_explanation

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("")
async def list_executions(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_auth),
    skill_id: Optional[int] = None,
    status: Optional[ExecutionStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List executions with pagination and filtering."""
    query = select(Execution).options(selectinload(Execution.skill))

    if user.role != UserRole.ADMIN:
        query = query.where(Execution.user_id == user.id)
    if skill_id:
        query = query.where(Execution.skill_id == skill_id)
    if status:
        query = query.where(Execution.status == status)

    total_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    query = query.order_by(Execution.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    executions = result.scalars().all()

    return {
        "items": [
            {
                "id": e.id,
                "skill_id": e.skill_id,
                "skill_name": e.skill.name if e.skill else None,
                "status": e.status.value,
                "input_params": json.loads(e.input_params),
                "output_result": json.loads(e.output_result) if e.output_result else None,
                "error_message": e.error_message,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in executions
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{execution_id}")
async def get_execution(
    execution_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_auth),
) -> dict:
    """Get execution detail."""
    query = select(Execution).options(selectinload(Execution.skill)).where(Execution.id == execution_id)
    if user.role != UserRole.ADMIN:
        query = query.where(Execution.user_id == user.id)

    result = await session.execute(query)
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return {
        "id": execution.id,
        "skill_id": execution.skill_id,
        "skill_name": execution.skill.name if execution.skill else None,
        "status": execution.status.value,
        "input_params": json.loads(execution.input_params),
        "output_result": json.loads(execution.output_result) if execution.output_result else None,
        "error_message": execution.error_message,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "created_at": execution.created_at.isoformat(),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_execution(
    payload: dict,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_auth),
) -> dict:
    """Create and start a new skill execution."""
    if "skill_id" not in payload:
        raise HTTPException(status_code=400, detail="Missing required field: skill_id")

    skill_result = await session.execute(select(Skill).where(Skill.id == payload["skill_id"]))
    skill = skill_result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    execution = Execution(
        skill_id=skill.id,
        user_id=user.id,
        status=ExecutionStatus.PENDING,
        input_params=json.dumps(payload.get("input_params", {})),
    )
    session.add(execution)
    await session.flush()

    audit = AuditLog(
        user_id=user.id,
        action="execute",
        resource_type="execution",
        resource_id=str(execution.id),
        details=json.dumps({"skill_id": skill.id, "skill_name": skill.name}),
    )
    session.add(audit)

    return {
        "id": execution.id,
        "skill_id": execution.skill_id,
        "status": execution.status.value,
        "created_at": execution.created_at.isoformat(),
    }


@router.post("/{execution_id}/run")
async def run_execution(
    execution_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_auth),
) -> dict:
    """Run an execution (deterministic core, no LLM)."""
    query = select(Execution).options(selectinload(Execution.skill)).where(Execution.id == execution_id)
    if user.role != UserRole.ADMIN:
        query = query.where(Execution.user_id == user.id)

    result = await session.execute(query)
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if execution.status not in (ExecutionStatus.PENDING, ExecutionStatus.FAILED):
        raise HTTPException(status_code=400, detail=f"Cannot run execution in status: {execution.status.value}")

    execution.status = ExecutionStatus.RUNNING
    execution.started_at = datetime.now(timezone.utc)

    input_params = json.loads(execution.input_params)

    try:
        result_data = await run_skill_deterministic(execution.skill, input_params)
        execution.status = ExecutionStatus.COMPLETED
        execution.output_result = json.dumps(result_data)
        execution.completed_at = datetime.now(timezone.utc)
    except Exception as e:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = str(e)
        execution.completed_at = datetime.now(timezone.utc)

    audit = AuditLog(
        user_id=user.id,
        action="run",
        resource_type="execution",
        resource_id=str(execution.id),
        details=json.dumps({"status": execution.status.value}),
    )
    session.add(audit)

    return {
        "id": execution.id,
        "status": execution.status.value,
        "output_result": json.loads(execution.output_result) if execution.output_result else None,
        "error_message": execution.error_message,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
    }


@router.post("/{execution_id}/explain")
async def explain_execution(
    execution_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_auth),
) -> dict:
    """Generate an LLM explanation for a completed execution (opt-in, advisory)."""
    query = select(Execution).options(selectinload(Execution.skill)).where(Execution.id == execution_id)
    if user.role != UserRole.ADMIN:
        query = query.where(Execution.user_id == user.id)

    result = await session.execute(query)
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if execution.status != ExecutionStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Can only explain completed executions")

    if not execution.output_result:
        raise HTTPException(status_code=400, detail="Execution has no result to explain")

    input_params = json.loads(execution.input_params)
    deterministic_result = json.loads(execution.output_result)
    settings = get_settings()

    explanation_result = await generate_explanation(
        skill_name=execution.skill.name,
        skill_display_name=execution.skill.display_name,
        input_params=input_params,
        deterministic_result=deterministic_result,
        settings=settings,
    )

    # Store explanation in audit log
    audit = AuditLog(
        user_id=user.id,
        action="explain",
        resource_type="execution",
        resource_id=str(execution.id),
        details=json.dumps({"explanation_status": explanation_result.get("status")}),
    )
    session.add(audit)
    await session.commit()

    return {
        "execution_id": execution.id,
        "explanation": explanation_result,
    }


async def run_skill_deterministic(skill: Skill, input_params: dict) -> dict:
    """Run skill with deterministic core logic (no LLM required)."""
    schema = json.loads(skill.schema)
    skill_name = skill.name

    if skill_name == "locus-compare":
        return await run_locus_compare(input_params)
    elif skill_name == "field-onboarding":
        return await run_field_onboarding(input_params)
    else:
        return {
            "status": "completed",
            "message": f"Skill '{skill_name}' executed (stub)",
            "input_received": input_params,
            "output": {"result": "placeholder"},
        }


async def run_locus_compare(input_params: dict) -> dict:
    """Deterministic locus compare workflow (stub with realistic structure)."""
    required = ["chromosome", "start", "end", "sentinel_snp", "population"]
    for field in required:
        if field not in input_params:
            raise ValueError(f"Missing required parameter: {field}")

    return {
        "status": "completed",
        "workflow": "locus-compare",
        "steps": {
            "gwas_fetch": {"status": "completed", "variants_found": 1247},
            "eqtl_fetch": {"status": "completed", "variants_found": 892},
            "ld_compute": {"status": "completed", "variants_with_ld": 856},
            "render": {"status": "completed", "plot_path": "/tmp/locus_compare.png", "panels": 4},
        },
        "output": {
            "plot_url": "/api/executions/{id}/plot",
            "summary": "Locus compare plot generated with 4 panels: GWAS, eQTL, LD, Combined",
            "palindromic_excluded": 23,
        },
    }


async def run_field_onboarding(input_params: dict) -> dict:
    """Deterministic field onboarding workflow (stub with realistic structure)."""
    if "topic" not in input_params:
        raise ValueError("Missing required parameter: topic")

    topic = input_params["topic"]
    mode = input_params.get("mode", "onboard")

    return {
        "status": "completed",
        "workflow": "field-onboarding",
        "topic": topic,
        "mode": mode,
        "steps": {
            "prerequisites": {
                "frameworks": [
                    {"name": "Statistical Genetics", "status": "used"},
                    {"name": "Population Genetics", "status": "learned"},
                    {"name": "GWAS Methodology", "status": "new"},
                ],
                "assessment_complete": True,
            },
            "maturity": "emerging",
            "ladder": [
                {"rung": 1, "name": "Motivation", "complete": True},
                {"rung": 2, "name": "Vocabulary Map", "complete": True},
                {"rung": 3, "name": "Core Framework", "complete": False},
                {"rung": 4, "name": "Methods in Practice", "complete": False},
                {"rung": 5, "name": "Frontier & Reading Path", "complete": False},
            ],
            "diagnostic_questions": [
                "What is the difference between linkage disequilibrium and correlation?",
                "How does population stratification confound GWAS?",
            ],
        },
        "output": {
            "reading_path": [
                "Visscher et al. 2017 - 10 Years of GWAS Discovery",
                "Tam et al. 2019 - Benefits and limitations of GWAS",
            ],
        },
    }