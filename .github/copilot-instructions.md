# CBaaS (Chatbot-as-a-Service) - AI Agent Instructions

## Project Overview
CBaaS is a multi-tenant RAG (Retrieval-Augmented Generation) SaaS platform. Django REST backend with React/TypeScript frontend, deployed to AWS ECS with CI/CD via GitHub Actions.

## Architecture

### Tech Stack
- **Backend**: Django 4.x + DRF, PostgreSQL with pgvector, Celery + Redis
- **Frontend**: React 18 + TypeScript, Redux Toolkit, Vite, shadcn/ui
- **Infrastructure**: Docker, AWS ECS, ECR
- **AI/ML**: Multi-provider LLM support (OpenAI, Gemini, DeepSeek), vector embeddings

### Key Components
```
backend/
  apps/               # Django apps (auth, chat, chatbot, documents, search, etc.)
  common/             # Shared utilities (llm/, middleware/, utils/)
  config/             # Settings split by environment (dev/staging/prod)
frontend/
  src/
    apis/             # Raw HTTP clients (axios-based)
    services/         # Business logic layer (wraps APIs)
    store/            # Redux slices + middleware
infra/ecs/            # ECS task definitions
```

## Critical Patterns

### Backend

**1. Environment-Based Settings**
Settings are loaded via `DJANGO_ENV` variable in `config/settings.py`:
```python
# Loads from config/environments/{dev,staging,prod}.py
DJANGO_ENV = os.environ.get("DJANGO_ENV", "dev")
```
- Dev: `DEBUG=True`, `SERVE_STATIC_FILES=True`, local DB
- Prod: `DEBUG=True` (error tracking), `SERVE_STATIC_FILES=False`, S3 storage, Gunicorn
- **Key**: `SERVE_STATIC_FILES` controls file serving, decoupled from `DEBUG`

**2. Multi-Provider LLM Architecture**
LLM providers are abstracted in `common/llm/`:
- `embeddings.py`: Provider-agnostic embedding function with OpenAI/Gemini support
- Apps like `chatbot` use `ProviderTestService` class to validate API keys
- Provider selection via settings: `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIM` (default 1536)

**3. Vector Search with pgvector**
- `apps/documents/models.py`: `DocumentChunk` has `VectorField(dimensions=1536)` for embeddings
- Migrations include pgvector extension setup and IVFFlat index creation
- Search via cosine similarity in `apps/search/`

**4. Static & Media File Storage**
Environment-specific file serving decoupled from DEBUG:
- **Development**: Local filesystem (`SERVE_STATIC_FILES=True`, files at `staticfiles/` and `media/`)
- **Production**: AWS S3 (`SERVE_STATIC_FILES=False`) via custom backends in `common/storage_backends.py`
  - `StaticStorage`: Static files at `s3://{bucket}/static/` (public-read, overwrite enabled)
  - `MediaStorage`: User uploads at `s3://{bucket}/media/` (private, no overwrite)
- URLs served via `SERVE_STATIC_FILES` check in `config/urls.py` (dev only) or S3 direct URLs (prod)
- **Critical**: `DEBUG=True` in all environments for error tracking, but `SERVE_STATIC_FILES` controls file serving

**5. Async Task Processing**
- Celery configured in `config/celery.py` with namespace "CELERY"
- Document processing tasks in `apps/documents/tasks.py` (extract text, generate embeddings, chunk)
- Worker uses same `Dockerfile.prod` as web service, different CMD

**6. Request Logging Middleware**
Custom middleware in `common/middleware/logging_middleware.py`:
- Generates unique `request_id` for tracing
- Logs request/response with sanitized headers/body
- Configurable exclusions for static files, health checks
- Structured logging to `logs/requests.log`

**7. JWT Authentication**
- Uses `djangorestframework-simplejwt` with blacklist support
- Login view in `apps/auth/login/views.py` returns `access` + `refresh` tokens
- Custom throttling via `ScopedThrottle` class per endpoint

**8. Global Exception Handler (CRITICAL)**
**All API errors are automatically handled - never return raw Django errors!**

Custom exception handler in `common/exceptions/handlers.py`:
- Catches: `IntegrityError`, `ValidationError`, `ValueError`, `TypeError`, all exceptions
- Returns consistent JSON: `{error: string, detail: any, type: string}`
- Configured in `REST_FRAMEWORK` settings as `EXCEPTION_HANDLER`

**Error response format:**
```python
{
    "error": "User-friendly message",           # Required: displayed to user
    "detail": "Additional context or dict",     # Optional: technical details
    "type": "IntegrityError"                    # Optional: error classification
}
```

**Examples:**
- IntegrityError (duplicate email) → `"This email address is already registered."`
- ValidationError → Field-specific validation messages
- 404/403/500 → Appropriate user-friendly messages

**The handler automatically:**
- Parses database constraint violations into readable text
- Logs all exceptions with full tracebacks
- Returns proper HTTP status codes (400 for client errors, 500 for server errors)
- Never returns HTML error pages to API clients

**Adding new error types:**
Edit `common/exceptions/handlers.py` and add handling logic. Frontend will automatically display the message via `getErrorMessage()` utility.

**Documentation:** See `docs/GLOBAL_ERROR_HANDLING.md`

### Frontend

**1. Service Layer Pattern**
Never call APIs directly from components. Use services in `src/services/`:
```typescript
// ❌ Don't: import LoginAPI from 'apis/auth/LoginAPI'
// ✅ Do: import { AuthService } from 'services/auth/authService'
```
- Services handle token storage, error formatting, business logic
- APIs in `src/apis/` are thin wrappers around axios

**2. Redux State Management**
- Redux Toolkit with `redux-persist` (only `auth` slice persisted)
- Middleware in `store/middleware/authMiddleware.ts` handles token refresh/logout
- Slices: `authSlice`, `userSlice`, `uiSlice`
- **No RTK Query** - use service layer instead

**3. Environment Variables**
- `.env.development` and `.env.production` are committed (non-sensitive config only)
- Vite automatically loads based on `mode` (dev/production)
- Access via `import.meta.env.VITE_API_BASE_URL`

**4. Global Error Handling (CRITICAL)**
**Always use the global error handling system - never parse errors manually!**

The project has a complete error handling infrastructure:

**Backend:** Global exception handler in `common/exceptions/handlers.py`
- Catches all exceptions (IntegrityError, ValidationError, etc.)
- Returns consistent JSON format: `{error: string, detail: any, type: string}`
- Configured in `config/environments/base.py` as `EXCEPTION_HANDLER`

**Frontend:** Axios interceptor + error utilities
- **Interceptor** (`apis/configs/axiosConfig.ts`): Automatically parses all API errors
- **Utility** (`apis/configs/axiosUtils.ts`): Provides `getErrorMessage()` helper

**✅ ALWAYS use this pattern:**
```typescript
import { getErrorMessage } from '@/apis/configs/axiosUtils';

try {
  await someAPICall();
} catch (error) {
  const errorMessage = getErrorMessage(error, 'Friendly fallback message');
  toast({ title: "Error", description: errorMessage, variant: "destructive" });
}
```

**❌ NEVER parse errors manually:**
```typescript
// DON'T DO THIS!
catch (error: any) {
  const msg = error.response?.data?.error || error.response?.data?.message || 'Error';
  toast.error(msg);
}
```

**Why this matters:**
- ✅ Consistent error messages across the app
- ✅ User-friendly text (no technical jargon)
- ✅ Type-safe with full TypeScript support
- ✅ Easy to maintain (update one file, affects all pages)
- ✅ Automatic parsing via Axios interceptor

**Available utilities in `axiosUtils.ts`:**
- `getErrorMessage(error, fallback?)` - Extract user-friendly message
- `getErrorDetails(error)` - Get detailed error info for debugging
- `isErrorStatus(error, status)` - Check specific HTTP status
- `isNetworkError(error)` - Detect network errors

**Documentation:** See `docs/GLOBAL_ERROR_HANDLING.md` for complete guide

## Development Workflows

### Docker Commands
Use `docker-compose.dev.yml` for local dev:
```bash
# Start all services (web, worker, db, redis, frontend)
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f web

# Run migrations
docker compose -f docker-compose.dev.yml exec web python manage.py migrate

# Rebuild after dependency changes
docker compose -f docker-compose.dev.yml up -d --build
```

**Important**: 
- Dev uses `Dockerfile.dev` (runserver, hot reload, volumes mounted)
- Prod uses `Dockerfile.prod` (Gunicorn, no volumes)
- Frontend dev runs on port 8080 (Vite), backend on 8000

### Testing
```bash
# Backend tests (inside container)
docker compose -f docker-compose.dev.yml exec web pytest

# Frontend tests
cd frontend && npm run test

# CI runs tests via .github/workflows/ci.yml on PR to main
```

### Database
- PostgreSQL with `pgvector` extension (ankane/pgvector image)
- Port 5433 (dev) to avoid conflicts with local PostgreSQL
- Health checks ensure DB is ready before migrations

## Deployment (CD Pipeline)

### GitHub Actions Workflow
`.github/workflows/cd.yml` triggers on push to `release` branch:
1. Build `frontend/Dockerfile.prod`, `backend/Dockerfile.prod` (worker uses same image)
2. Push to ECR: `577897067437.dkr.ecr.ap-south-1.amazonaws.com/{frontend,backend,worker}`
3. Force ECS service updates for frontend-service, backend-service, worker-service

**Critical**: 
- Both worker and web use `Dockerfile.prod` (CMD overridden in ECS task definition)
- CD uses hardcoded `ECR_REGISTRY` (GitHub Actions env vars can't reference each other)
- Frontend build embeds `.env.production` at build time (Vite static compilation)

### ECS Configuration
- Task definitions in `infra/ecs/` (currently placeholder)
- Cluster: `my-app-cluster`
- Services: `frontend-service`, `backend-service`, `worker-service`

## Common Pitfalls

1. **Frontend env vars**: Must prefix with `VITE_` to be accessible, embedded at build time (not runtime)
2. **Worker Dockerfile**: Always use `Dockerfile.prod`, override CMD (don't create separate Dockerfile.worker)
3. **pgvector migrations**: Ensure extension created before VectorField columns, dimension changes require data wipe
4. **Celery autodiscovery**: Tasks must be in `tasks.py` within Django apps for `app.autodiscover_tasks()` to work
5. **CORS**: Configured in `config/environments/base.py` with `django-cors-headers`

## Key Files Reference
- `backend/config/settings.py` - Environment router
- `backend/config/celery.py` - Celery app configuration
- `backend/common/llm/embeddings.py` - LLM provider abstraction
- `backend/common/exceptions/handlers.py` - Global exception handler
- `frontend/src/apis/configs/axiosConfig.ts` - Axios interceptor (auto error parsing)
- `frontend/src/apis/configs/axiosUtils.ts` - Error utilities (`getErrorMessage()`)
- `frontend/src/services/auth/authService.ts` - Auth flow example
- `frontend/src/store/index.ts` - Redux store config
- `docker-compose.{dev,prod}.yml` - Service orchestration
- `.github/workflows/{ci,cd}.yml` - CI/CD pipelines
- `docs/GLOBAL_ERROR_HANDLING.md` - Error handling documentation

## Conventions
- Backend apps use `services.py` for complex business logic (e.g., `ProviderTestService`)
- Frontend uses PascalCase for service classes, camelCase for methods
- Django models: Use UUIDs for primary keys, `created_at`/`updated_at` timestamps
- API responses: Consistent structure with `data`, `message`, `error` keys
- Logging: Use structured logging with `extra` dict for request context
- **Error Handling**: Always use `getErrorMessage()` in frontend, never parse errors manually
- **Backend Errors**: Let global exception handler format errors, return `{error, detail, type}` format
