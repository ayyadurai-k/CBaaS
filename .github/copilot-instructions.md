# Copilot Instructions for CBaaS


## Mission-Critical Coding Philosophy

Treat every coding task as a mission-critical, life-or-death operation. Code must be flawless—fully tested with unit, integration, and performance tests. Apply DRY (Don't Repeat Yourself) and KISS (Keep It Simple, Stupid) principles rigorously. Only write essential, efficient code—no redundancy, no overengineering. Handle edge cases precisely and validate all inputs to guard against security threats like SQLi, XSS, and CSRF. Code must be clean, minimal, and expressive. Prioritize clarity: use descriptive names, consistent formatting, and comments for non-obvious logic. Architect for scalability, modularity, and resilience. Optimize performance and memory—profile early, eliminate bottlenecks. Plan everything: system design, API contracts, database structure, and tools. Document APIs, configs, data flows, and deployment steps. Use centralized, secure error handling with graceful degradation. Never hardcode secrets—use environment configs and secret managers. Assume all code will be audited. Security is foundational. Plan and code as if survival depends on it—because in this room, it does.

Keep this in mind always.

## Custom Instructions

- Always use type annotations in Python functions.
- Prefer functional components in React.
- Use Tailwind utility classes for all new UI elements.
- Use Black for Python formatting and Prettier for frontend code.
- All new features require unit tests in `tests.py` (backend) or `__tests__/` (frontend).
- PRs should reference related issues and include a summary of changes.
- Backend errors: Use Django logging in `config/settings.py`.
- Frontend errors: Use `useError` hook in `frontend/src/hooks/useError.ts`.
- Celery tasks log to console and are monitored via Flower (optional).
- REST endpoints follow `/api/<app>/<resource>/` pattern.
- Use DRF serializers for input/output validation.
- Document new endpoints in `backend/apps/<app>/docs/`.
- Run backend tests: `pytest backend/`
- Run frontend tests: `bun test`
- CI pipeline defined in `.github/workflows/ci.yml`
- Secrets and sensitive configs must go in `.env.dev` (never commit secrets).
- Use Django’s `@login_required` and DRF permissions for protected endpoints.
- Always rebuild Docker images after changing dependencies.
- Ensure migrations are created and applied for new models.
- Use absolute imports in backend code for clarity.

## Project Architecture
- **Monorepo** with `backend` (Django, Celery, PostgreSQL, Redis) and `frontend` (React, Vite, Bun, Tailwind CSS).
- **Backend**: Django apps in `backend/apps/` (e.g., `api_keys`, `chat`, `chatbot`, `documents`, etc.), with shared code in `backend/common/` and configuration in `backend/config/`.
- **Frontend**: Modern React app in `frontend/` using Bun for package management and Vite for builds.
- **Services**: Docker Compose orchestrates `db` (pgvector), `redis`, `web` (Django), `worker` (Celery), and `frontend`.

## Developer Workflows
- **Backend**:
  - Run migrations: `python manage.py migrate`
  - Start server: `python manage.py runserver 0.0.0.0:8000`
  - Celery worker: `celery -A config.celery.app worker -l info`
  - Environment config: `.env.dev` in `backend/`
- **Frontend**:
  - Install deps: `bun install`
  - Start dev server: `bun dev --host 0.0.0.0 --port 5173`
- **Docker Compose**: Use `docker-compose.dev.yml` for local development. All services are health-checked and interdependent.

## Conventions & Patterns
- **Django apps**: Each app has `models.py`, `serializers.py`, `views.py`, `urls.py`, and `tests.py`.
- **Celery**: Tasks defined in app directories (e.g., `documents/tasks.py`).
- **Environment variables**: Managed via `.env.dev` for local/dev settings.
- **Frontend**: Uses shadcn-ui and Tailwind for UI, with code split into `components/`, `hooks/`, `lib/`, and `pages/`.
- **Volumes**: Persistent DB data via Docker volume `db_data`.

## Integration Points
- **Database**: PostgreSQL with pgvector extension for vector search.
- **Redis**: Used for caching and as Celery broker.
- **Celery**: Background tasks, started via Docker Compose or manually.
- **Frontend/Backend**: Communicate via REST APIs (Django views/serializers).

## Key Files & Directories
- `backend/apps/` — Django apps (business logic)
- `backend/common/` — Shared backend code
- `backend/config/` — Django/Celery config
- `frontend/` — React app
- `docker-compose.dev.yml` — Service orchestration
- `requirements/` — Python dependency management

## Example Patterns
- Add a Django app: create folder in `backend/apps/`, add `models.py`, `views.py`, etc., and register in `config/settings.py`.
- Add a Celery task: define in `<app>/tasks.py`, import in `config/celery.py`.
- Add a frontend component: place in `frontend/src/components/`, use Tailwind for styling.

## External Resources
- [Lovable Project Portal](https://lovable.dev/projects/b80c3f8e-cc02-48b8-9f5e-5c37f09dc7ac) for cloud editing/deployment.
- [Custom Domain Setup](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)

---
_If any section is unclear or missing, please provide feedback to improve these instructions._
