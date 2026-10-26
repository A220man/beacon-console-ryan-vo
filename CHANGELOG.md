# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added this round
- Frontend LLM explanation integration: Explain button on ExecutionDetailPage for completed executions
- Frontend API client: `explainExecution` method and `ExplanationResponse` type
- Explanation display card with advisory badge, provider/model metadata, skipped/error states

### Fixed
- Backend: All 63 tests pass including LLM explanation tests

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.0.0] - 2026-10-14

### Added
- Initial release of Beacon Console
- FastAPI backend with SQLAlchemy models (User, Skill, Execution, AuditLog)
- React + TypeScript + Vite frontend with typed API client
- OIDC authentication via Keycloak (Authorization Code + PKCE)
- HttpOnly cookie sessions with CSRF protection
- Role-based access control (viewer/operator/admin)
- Skill catalog CRUD with pagination, filtering, search
- Execution engine with deterministic offline core
- Statistical genetics locus compare workflow (4 primitives)
- Field onboarding guided workflow (5-rung ladder + decode mode)
- Opt-in LLM explanations for executions (OpenAI-compatible, Anthropic, Gemini, Ollama)
- Docker Compose with PostgreSQL, Redis, Keycloak
- Comprehensive test suite (backend pytest, frontend vitest)
- Health checks and audit logging
- Provider-agnostic LLM adapter framework

### Security
- No hardcoded secrets or credentials
- Tokens never logged
- Demo mode binds to localhost only
- Production mode refuses demo configuration

### Infrastructure
- Non-root Docker users
- .dockerignore for both services
- Healthchecks on all containers
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).