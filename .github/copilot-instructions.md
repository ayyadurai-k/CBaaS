# CBaaS (Chatbot-as-a-Service) - AI Agent Instructions

## 🎯 MISSION-CRITICAL CODING PHILOSOPHY

**TREAT EVERY CODING TASK AS A LIFE-OR-DEATH OPERATION**

Your code is mission-critical. Assume it will be audited, deployed to production immediately, and that lives depend on its correctness. Follow these non-negotiable principles:

### Code Quality Imperatives
- ✅ **Flawless Execution**: Write fully tested code (unit, integration, performance tests)
- ✅ **DRY Principle**: Don't Repeat Yourself—eliminate all redundancy
- ✅ **KISS Principle**: Keep It Simple, Stupid—no overengineering, only essential code
- ✅ **Zero Defects**: Handle ALL edge cases, validate ALL inputs
- ✅ **Security First**: Guard against SQLi, XSS, CSRF, injection attacks—security is foundational
- ✅ **Clean Code**: Minimal, expressive, readable—use descriptive names, consistent formatting
- ✅ **Documentation**: Comment non-obvious logic, document APIs, configs, data flows, deployment

### Architecture Requirements
- 🏗️ **Scalability**: Design for growth—assume 100x traffic tomorrow
- 🏗️ **Modularity**: Loosely coupled components, high cohesion
- 🏗️ **Resilience**: Graceful degradation, circuit breakers, retries
- 🏗️ **Performance**: Profile early, eliminate bottlenecks, optimize memory
- 🏗️ **Planning**: Design system architecture, API contracts, database schemas upfront

### Security & Configuration
- 🔒 **No Hardcoded Secrets**: Use environment variables and secret managers
- 🔒 **Centralized Error Handling**: Global exception handlers with graceful degradation
- 🔒 **Input Validation**: Sanitize and validate EVERYTHING from external sources
- 🔒 **Principle of Least Privilege**: Minimal permissions, secure defaults

### Testing Standards
- 🧪 **Unit Tests**: Every function, every method, every edge case
- 🧪 **Integration Tests**: API endpoints, service interactions, database operations
- 🧪 **Performance Tests**: Load testing, profiling, bottleneck identification
- 🧪 **Security Tests**: Penetration testing, vulnerability scanning

**Remember**: Plan and code as if survival depends on it—because in production, it does.

---

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

**8. API Documentation (drf-spectacular)**
**All API endpoints must be documented with `@extend_schema` decorator:**

```python
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

class SignupView(APIView):
    @extend_schema(
        request=SignupSerializer,
        responses={
            201: OpenApiResponse(
                description="User successfully registered",
                response={"type": "object", "properties": {...}},
                examples=[OpenApiExample("Success", value={...})]
            ),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Authentication"],
        summary="Register a new user"
    )
    def post(self, request):
        ...
```

**Key points:**
- Use `@extend_schema` on all API methods (post, get, put, patch, delete)
- Specify `request` serializer for request body documentation
- Define all possible `responses` with status codes
- Add examples for success and error cases
- Group endpoints with `tags`
- Add descriptive `summary` and `description`

**9. Django Model Patterns**
**Follow these conventions for all Django models:**

```python
import uuid
from django.db import models

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["name"]),
        ]
        
    def __str__(self):
        return self.name
```

**Conventions:**
- **Primary Keys**: Always use `UUIDField` (not auto-incrementing integers)
- **Timestamps**: Include `created_at` (auto_now_add) and `updated_at` (auto_now) on all models
- **Indexes**: Add explicit indexes for frequently queried fields
- **Choices**: Use `models.TextChoices` or `models.IntegerChoices` enums
- **Foreign Keys**: Always specify `on_delete` behavior (CASCADE, PROTECT, SET_NULL)
- **Related Names**: Use descriptive `related_name` for reverse relations
- **Meta**: Define ordering, unique_together, indexes in Meta class
- **String Representation**: Always implement `__str__()` method

**10. DRF Serializer Patterns**
**Use appropriate serializer types for different operations:**

```python
from rest_framework import serializers

# For reading/listing (includes all fields, nested serializers)
class ChatbotSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = Chatbot
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

# For creating/updating (specific fields only)
class ChatbotUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chatbot
        fields = ['name', 'description', 'temperature']
        
    def validate_temperature(self, value):
        if not 0 <= value <= 2:
            raise serializers.ValidationError("Temperature must be between 0 and 2")
        return value

# For simple operations (no model)
class TestKeySerializer(serializers.Serializer):
    provider = serializers.CharField()
    api_key = serializers.CharField()
```

**Naming conventions:**
- `<Model>Serializer`: Full serializer for GET requests
- `<Model>UpdateSerializer`: Partial serializer for PUT/PATCH
- `<Model>CreateSerializer`: Serializer for POST (if different from update)
- `<Action>Serializer`: For non-model operations (e.g., `TestKeySerializer`)

**11. Service Layer Pattern**
**Complex business logic belongs in service classes, not views:**

```python
# apps/chatbot/services.py
class ProviderTestService:
    """Service to test different LLM providers with their API keys."""
    
    @classmethod
    def test_provider(cls, provider: str, model_name: str, api_key: str) -> Tuple[bool, str, Dict]:
        """Test if the provider API key and model work correctly."""
        try:
            if provider == "openai":
                return cls._test_openai(model_name, api_key)
            # ... more logic
        except Exception as e:
            logger.error(f"Error testing {provider}: {str(e)}")
            return False, f"Provider test failed: {str(e)}", {"error": str(e)}
```

**When to use services:**
- Multi-step operations (e.g., create chatbot + configure models)
- External API calls (LLM providers, S3 operations)
- Complex validation logic
- Reusable business logic across multiple views
- Operations that span multiple models

**Views should be thin - delegate to services:**
```python
class TestApiKeyView(APIView):
    def post(self, request):
        serializer = TestKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Delegate to service
        success, message, details = ProviderTestService.test_provider(
            serializer.validated_data['provider'],
            serializer.validated_data['model'],
            serializer.validated_data['api_key']
        )
        
        return Response({"success": success, "message": message, "details": details})
```

**12. Celery Task Patterns**
**Async tasks for long-running operations:**

```python
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_document(self, document_id: str):
    """
    Process uploaded document: extract text, chunk, generate embeddings.
    
    Args:
        self: Celery task instance (bind=True)
        document_id: UUID of document to process
    """
    try:
        document = Document.objects.get(id=document_id)
        document.status = Document.Status.PROCESSING
        document.save()
        
        # Extract text
        content = extract_text_from_bytes(document_bytes)
        
        # Chunk text
        chunks = chunk_text(content)
        
        # Generate embeddings
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            DocumentChunk.objects.create(
                document=document,
                chunk_index=i,
                content=chunk,
                embedding=embedding
            )
        
        document.status = Document.Status.READY
        document.save()
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        document.status = Document.Status.FAILED
        document.save()
        raise  # Re-raise for Celery retry mechanism
```

**Task conventions:**
- Use `@shared_task` decorator (not `@app.task`)
- Set `bind=True` to access task instance (`self`)
- Configure retry: `autoretry_for`, `retry_backoff`, `max_retries`
- Add detailed docstrings with parameter descriptions
- Log errors before re-raising
- Update model status (PROCESSING → READY/FAILED)
- Tasks must be in `tasks.py` within Django apps for autodiscovery

**13. Global Exception Handler (CRITICAL)**
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

**5. Toast Notifications**
**Use the correct toast library based on context:**

The project uses **TWO different toast systems**:

**shadcn/ui Toast (`@/hooks/use-toast`)** - For application pages:
```typescript
import { toast } from '@/hooks/use-toast';

toast({
  title: "Success",
  description: "Operation completed successfully",
  variant: "default" // or "destructive" for errors
});
```

**Sonner (`sonner`)** - For auth pages only:
```typescript
import { toast } from 'sonner';

toast.success('Account created successfully!');
toast.error('Login failed');
```

**⚠️ IMPORTANT:** 
- Use `@/hooks/use-toast` for ALL application pages (Dashboard, Documents, Settings, etc.)
- Use `sonner` ONLY for auth pages (Login, Signup, ForgotPassword, ResetPassword)
- Never mix toast libraries in the same component

**6. Redux Patterns**
**Always use typed hooks for Redux:**

```typescript
// ❌ DON'T use raw hooks
import { useDispatch, useSelector } from 'react-redux';

// ✅ DO use typed hooks
import { useAppDispatch, useAppSelector } from '@/store/hooks';

const dispatch = useAppDispatch();
const user = useAppSelector((state) => state.user.profile);
```

**Custom Hooks for Common Operations:**
- **`useAuth()`** from `@/hooks/redux/useAuth` - Authentication state and actions
- **`useProfile()`** from `@/hooks/redux/useProfile` - User profile management
- **`useOrganization()`** from `@/hooks/useOrganization` - Organization management

**Example:**
```typescript
import { useAuth } from '@/hooks/redux/useAuth';
import { useProfile } from '@/hooks/redux/useProfile';

const { isAuthenticated, login, logout } = useAuth();
const { profile, updateProfile, uploadProfilePicture } = useProfile();
```

**7. UI Components (shadcn/ui)**
**Always use shadcn/ui components from `@/components/ui`:**

```typescript
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
```

**Component Styling:**
- Use Tailwind CSS classes for styling
- Use `cn()` utility from `@/lib/utils` for conditional classes
- Follow shadcn/ui variant patterns (e.g., `variant="destructive"`)

**Example:**
```typescript
import { cn } from '@/lib/utils';

<Button 
  variant="destructive" 
  className={cn("w-full", isLoading && "opacity-50")}
>
  Delete
</Button>
```

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
- `backend/common/middleware/logging_middleware.py` - Request logging middleware
- `backend/apps/chatbot/services.py` - Service layer example (ProviderTestService)
- `backend/apps/documents/tasks.py` - Celery task example (process_document)
- `frontend/src/apis/configs/axiosConfig.ts` - Axios interceptor (auto error parsing)
- `frontend/src/apis/configs/axiosUtils.ts` - Error utilities (`getErrorMessage()`)
- `frontend/src/services/auth/authService.ts` - Auth flow example
- `frontend/src/store/index.ts` - Redux store config
- `frontend/src/hooks/redux/useAuth.ts` - Custom Redux hook example
- `docker-compose.{dev,prod}.yml` - Service orchestration
- `.github/workflows/{ci,cd}.yml` - CI/CD pipelines
- `docs/GLOBAL_ERROR_HANDLING.md` - Error handling documentation

## Conventions
- **Backend Services**: Use `services.py` for complex business logic (e.g., `ProviderTestService`)
- **Frontend Services**: PascalCase for service classes, camelCase for methods
- **Django Models**: Use UUIDs for primary keys, `created_at`/`updated_at` timestamps, `TextChoices` for enums
- **DRF Serializers**: `<Model>Serializer` for GET, `<Model>UpdateSerializer` for PUT/PATCH, `<Action>Serializer` for operations
- **API Documentation**: All endpoints must have `@extend_schema` decorator with examples
- **Celery Tasks**: Use `@shared_task(bind=True, autoretry_for=...)` in `tasks.py` files
- **API Responses**: Consistent structure with `data`, `message`, `error` keys
- **Logging**: Use structured logging with `extra` dict for request context
- **Error Handling (Frontend)**: Always use `getErrorMessage()`, never parse errors manually
- **Error Handling (Backend)**: Let global exception handler format errors, return `{error, detail, type}` format
- **Toast Notifications**: Use shadcn/ui toast for app pages, Sonner for auth pages only
- **Redux Hooks**: Always use `useAppDispatch()`/`useAppSelector()`, never raw Redux hooks
- **UI Components**: Use shadcn/ui components from `@/components/ui`, style with Tailwind CSS
