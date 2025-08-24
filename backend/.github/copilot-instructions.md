# CBaaS (Chatbot-as-a-Service) AI Development Guide

## Project Overview
CBaaS is a Django-based chatbot service platform that provides:
- Multi-provider chat completion API with streaming support
- Document management with text extraction and embedding
- Organization and user management with JWT authentication
- API key management for client access
- Asynchronous document processing with Celery

## Architecture & Components

### Core Services
- **Web Service** (`web`): Django REST API server
- **Worker** (`worker`): Celery worker for async tasks
- **Database** (`db`): PostgreSQL with pgvector for embeddings
- **Cache** (`redis`): Redis for Celery broker and JWT blacklist

### Key Apps
- `chat/`: Chat completion APIs with streaming (`ChatCompletionsView`, `ChatStreamView`)
- `documents/`: Document management with async processing (`DocumentListCreateView`)
- `chatbot_provider/`: LLM provider configuration (`ChatbotProviderUpsertView`)
- `api_keys/`: API key management for client authentication
- `common/llm/`: Provider client implementations (OpenAI, Gemini, DeepSeek)

## Development Workflows

### Environment Setup
```bash
# Start all services
docker-compose up -d

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Authentication Flow
1. Register via `/api/v1/auth/signup/`
2. Login via `/api/v1/auth/login/` to get JWT tokens
3. Use tokens in `Authorization: Bearer <token>` header

### Document Processing
1. Upload via `POST /api/v1/documents/`
2. Async processing triggered automatically
3. Monitor status via `GET /api/v1/documents/{id}/`

## Project Conventions

### Security Patterns
- API keys are encrypted at rest using `common/security/encryption.py`
- Provider credentials stored per-organization with encryption
- Rate limiting applied to auth endpoints (`ScopedThrottle`)

### Error Handling
- Use `common/utils/circuit_breaker.py` for external service calls
- Standard error responses via DRF exception handlers
- Idempotency support via `common/utils/idempotency.py`

### API Patterns
- SSE streaming for chat completions
- Pagination via `common/core/pagination.py`
- Query filtering via `common/core/filters.py`

## Testing & Quality
- Run tests: `docker-compose exec web python manage.py test`
- Health checks: `/healthz` and `/readyz`
- API docs: `/api/docs/` (using drf-spectacular)
