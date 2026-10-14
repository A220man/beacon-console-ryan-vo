# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

oidc-auth

## Roadmap

### core-skeleton — Core FastAPI/React skeleton with health check

Status: done

Acceptance:
- FastAPI app starts and serves /health endpoint
- React + Vite frontend builds and serves
- Docker Compose brings up backend, frontend, Keycloak, PostgreSQL
- Backend and frontend tests run

Implementation: `backend/app/main.py`, `backend/app/api/health.py`, `backend/requirements.txt`, `backend/Dockerfile`, `frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/Dockerfile`, `docker-compose.yaml`, `.env.example`

Tests: `backend/tests/test_health.py`, `frontend/src/App.test.tsx`

### oidc-auth — OIDC authentication with Keycloak

Status: done

Acceptance:
- Login redirects to Keycloak
- Callback exchanges code for tokens
- Protected endpoints reject unauthenticated requests
- Logout clears session and redirects to Keycloak logout

Implementation: `backend/app/api/auth.py`, `backend/app/core/security.py`, `backend/app/core/config.py`, `keycloak/realm-export.json`

Tests: `backend/tests/test_auth.py`

### skill-catalog — Skill catalog CRUD and search

Status: done

Acceptance:
- List skills with pagination and filtering
- Create/update/delete skills (admin)
- Search skills by name, category, tags
- View skill detail with metadata

Implementation: `backend/app/api/skills.py`, `backend/app/models/__init__.py`, `frontend/src/pages/SkillsPage.tsx`, `frontend/src/pages/SkillDetailPage.tsx`

Tests: `backend/tests/test_skills.py`

### skill-execution — Skill execution engine with deterministic core

Status: done

Acceptance:
- Execute skill with input parameters
- Track execution status and results
- Deterministic offline mode works without LLM key
- LLM explanations opt-in, labeled advisory

Implementation: `backend/app/api/executions.py`, `backend/app/models/__init__.py`, `frontend/src/pages/ExecutionsPage.tsx`, `frontend/src/pages/ExecutionDetailPage.tsx`

Tests: `backend/tests/test_executions.py`

### genetics-workflow — Statistical genetics locus compare workflow

Status: done

Acceptance:
- Fetch GWAS catalog data for region
- Fetch eQTL catalogue data for region
- Compute LD from 1000 Genomes
- Render locus compare plot (4 panels)

Implementation: `backend/app/api/executions.py:run_locus_compare`

Tests: `backend/tests/test_executions.py::TestDeterministicExecution::test_locus_compare_deterministic`

### field-onboarding — Field onboarding guided workflow

Status: done

Acceptance:
- Prerequisite framework assessment
- Field maturity classification (settled/emerging/contested)
- Ladder progression: motivation → vocabulary → framework → methods → frontier
- Decode mode for passage analysis

Implementation: `backend/app/api/executions.py:run_field_onboarding`

Tests: `backend/tests/test_executions.py::TestDeterministicExecution::test_field_onboarding_deterministic`

