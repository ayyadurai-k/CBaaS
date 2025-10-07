# CBaaS - Chatbot as a Service

<div align="center">

![CBaaS Logo](./frontend/public/favicon.ico)

**A Multi-Tenant RAG-Powered SaaS Platform for Building Intelligent Chatbots**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-4.x-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/react-18.x-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.x-blue.svg)](https://www.typescriptlang.org/)

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Deployment](#-deployment)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Environment Variables](#-environment-variables)
- [API Documentation](#-api-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

**CBaaS (Chatbot-as-a-Service)** is a production-ready, multi-tenant SaaS platform that enables organizations to build, deploy, and manage AI-powered chatbots with Retrieval-Augmented Generation (RAG) capabilities. The platform supports multiple LLM providers, vector-based semantic search, and comprehensive document processing.

### Key Highlights

- 🤖 **Multi-Provider LLM Support**: Seamlessly integrate OpenAI, Google Gemini, DeepSeek, and more
- 📚 **RAG Implementation**: Advanced retrieval-augmented generation using pgvector for semantic search
- 🏢 **Multi-Tenancy**: Full organizational isolation with role-based access control
- 📄 **Document Intelligence**: Extract and process PDFs, DOCX, and text files for knowledge bases
- 🔐 **Enterprise Security**: JWT authentication, request throttling, and comprehensive logging
- ☁️ **Cloud-Native**: Docker-based deployment to AWS ECS with CI/CD via GitHub Actions
- ⚡ **Async Processing**: Celery-powered background tasks for document processing and embeddings

---

## ✨ Features

### Core Capabilities

#### 🤖 Chatbot Management
- Create and configure multiple chatbots per organization
- Customize chatbot behavior, personality, and knowledge sources
- API key management with provider validation
- Real-time chat interfaces with streaming support

#### 📊 RAG & Vector Search
- Automatic document chunking and embedding generation
- Semantic search using PostgreSQL pgvector extension
- Configurable embedding models (OpenAI, Gemini)
- IVFFlat indexing for efficient similarity search

#### 👥 Multi-Tenancy & Organizations
- Complete data isolation between organizations
- Role-based permissions (Owner, Admin, Member)
- Organization-level API key management
- User invitation and onboarding workflows

#### 📁 Document Processing
- Support for PDF, DOCX, TXT file uploads
- Async text extraction and chunking
- Automatic embedding generation via Celery workers
- S3-compatible storage (local/AWS)

#### 🔒 Security & Authentication
- JWT-based authentication with token blacklisting
- Refresh token rotation
- Request throttling per endpoint
- Comprehensive audit logging
- Middleware-based request/response tracking

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│                 │      │                  │      │                 │
│  React Frontend │─────▶│  Django Backend  │─────▶│   PostgreSQL    │
│   (Vite + TS)   │      │   (DRF + JWT)    │      │  + pgvector     │
│                 │      │                  │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
            ┌──────────────┐ ┌────────┐ ┌────────────┐
            │    Celery    │ │ Redis  │ │ LLM APIs   │
            │   Workers    │ │ Cache  │ │ (Multiple) │
            └──────────────┘ └────────┘ └────────────┘
```

### Multi-Provider LLM Architecture

The platform abstracts LLM provider complexity through a unified interface:

```python
# backend/common/llm/embeddings.py
get_embedding(text, provider="openai", model="text-embedding-3-small")
```

Supported providers:
- **OpenAI**: GPT-4, GPT-3.5-turbo, text-embedding-3-small/large
- **Google Gemini**: gemini-pro, gemini-pro-vision
- **DeepSeek**: deepseek-chat, deepseek-coder
- Extensible for custom providers

### Request Flow

```
User Request → Nginx/CloudFront → Django → Middleware Stack → View → Service Layer
                                                                       │
                                    ┌──────────────────────────────────┘
                                    │
                                    ├─▶ Database (PostgreSQL)
                                    ├─▶ Cache (Redis)
                                    ├─▶ Task Queue (Celery)
                                    └─▶ External APIs (LLMs)
```

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 4.x + Django REST Framework
- **Database**: PostgreSQL 15+ with pgvector extension
- **Task Queue**: Celery with Redis broker
- **Authentication**: djangorestframework-simplejwt
- **Storage**: S3-compatible (django-storages + boto3)
- **API Docs**: drf-spectacular (OpenAPI 3.0)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **State Management**: Redux Toolkit
- **UI Components**: shadcn/ui + Radix UI
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Routing**: React Router v6

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Orchestration**: AWS ECS (Fargate)
- **CI/CD**: GitHub Actions
- **Registry**: Amazon ECR
- **CDN**: CloudFront (frontend)
- **Reverse Proxy**: Nginx (production)

### Development Tools
- **Testing**: pytest (backend), Vitest (frontend)
- **Linting**: ESLint, Ruff
- **Type Checking**: mypy, TypeScript
- **Documentation**: Markdown + OpenAPI

---

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (for local development)
- **Git**
- **Python 3.12+** (optional, for local testing)
- **Node.js 18+** (optional, for frontend development)

### One-Command Setup

Clone the repository and start all services:

```bash
# Clone the repository
git clone https://github.com/ayyadurai-k/CBaaS.git
cd CBaaS

# Start all services with Docker Compose
docker compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy (~30 seconds)
# Backend will auto-migrate database on startup
```

**Services will be available at:**
- 🌐 Frontend: http://localhost:8080
- 🔧 Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/api/schema/swagger-ui/
- 🗄️ PostgreSQL: localhost:5433
- 🔴 Redis: localhost:6379

### Create a Superuser

```bash
# Access the backend container
docker compose -f docker-compose.dev.yml exec web bash

# Create superuser
python manage.py createsuperuser

# Access Django admin at http://localhost:8000/admin
```

### Stop Services

```bash
docker compose -f docker-compose.dev.yml down

# To remove volumes (deletes database data):
docker compose -f docker-compose.dev.yml down -v
```

---

## 📂 Project Structure

```
CBaaS/
├── backend/                    # Django backend application
│   ├── apps/                   # Django apps
│   │   ├── auth/              # Authentication (login, signup, reset)
│   │   ├── chat/              # Chat sessions and messages
│   │   ├── chatbot/           # Chatbot configuration
│   │   ├── documents/         # Document upload and processing
│   │   ├── search/            # Vector search implementation
│   │   ├── organizations/     # Multi-tenant organization management
│   │   ├── users/             # User profiles and management
│   │   └── api_keys/          # API key management
│   ├── common/                # Shared utilities
│   │   ├── llm/               # LLM provider abstraction
│   │   ├── middleware/        # Custom middleware (logging, auth)
│   │   ├── security/          # Security utilities
│   │   ├── services/          # Shared service classes
│   │   └── utils/             # Helper functions
│   ├── config/                # Django settings
│   │   ├── environments/      # Environment-specific configs (dev/staging/prod)
│   │   ├── settings.py        # Settings router
│   │   ├── celery.py          # Celery configuration
│   │   └── urls.py            # Root URL configuration
│   ├── requirements/          # Python dependencies
│   │   ├── base.txt           # Common dependencies
│   │   ├── dev.txt            # Development dependencies
│   │   └── prod.txt           # Production dependencies
│   ├── Dockerfile.dev         # Development Docker image
│   ├── Dockerfile.prod        # Production Docker image (web + worker)
│   └── manage.py              # Django management script
│
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── apis/              # Raw HTTP clients (axios)
│   │   ├── services/          # Business logic layer (wraps APIs)
│   │   ├── store/             # Redux state management
│   │   │   ├── slices/        # Redux slices (auth, user, ui)
│   │   │   └── middleware/    # Custom middleware (token refresh)
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── lib/               # Utility functions
│   │   └── constants/         # App constants
│   ├── public/                # Static assets
│   ├── Dockerfile.dev         # Development Docker image
│   ├── Dockerfile.prod        # Production Docker image (Nginx)
│   ├── .env.development       # Development environment config
│   ├── .env.production        # Production environment config
│   └── vite.config.ts         # Vite configuration
│
├── infra/                      # Infrastructure as Code
│   ├── aws/                   # AWS deployment scripts
│   │   ├── setup-aws-infrastructure.sh  # AWS resource creation
│   │   ├── deploy_frontend.sh           # Frontend deployment script
│   │   ├── deploy_backend.sh            # Backend deployment script
│   │   └── *.json             # ECS task definitions
│   └── ecs/                   # ECS configuration (placeholder)
│
├── docs/                       # Documentation
│   ├── README_DEPLOY_FRONTEND.md  # Frontend deployment guide
│   ├── README_DEPLOY_BACKEND.md   # Backend deployment guide
│   └── DOCKER_COMMANDS.md         # Docker reference
│
├── .github/                    # GitHub configuration
│   ├── workflows/             # CI/CD pipelines
│   │   ├── ci.yml             # Continuous Integration
│   │   └── cd.yml             # Continuous Deployment
│   └── copilot-instructions.md # AI agent instructions
│
├── docker-compose.dev.yml     # Development compose file
├── docker-compose.prod.yml    # Production compose file (local)
├── pytest.ini                 # Pytest configuration
└── README.md                  # This file
```

---

## 💻 Development

### Backend Development

#### Environment Variables

Create `backend/.env.dev`:

```env
# Django
DJANGO_ENV=dev
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,web

# Database
POSTGRES_DB=cbaas
POSTGRES_USER=cbaas
POSTGRES_PASSWORD=cbaas
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# LLM Configuration
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# AWS (for production)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=ap-south-1
```

#### Running Migrations

```bash
# Auto-run on container start, or manually:
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
```

#### Creating Migrations

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py makemigrations
```

#### Django Shell

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py shell
```

#### View Logs

```bash
# All services
docker compose -f docker-compose.dev.yml logs -f

# Specific service
docker compose -f docker-compose.dev.yml logs -f web
docker compose -f docker-compose.dev.yml logs -f worker
```

### Frontend Development

#### Environment Variables

Frontend uses Vite's environment system. Files are committed (non-sensitive config only):

**`.env.development`:**
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=CBaaS Development
```

**`.env.production`:**
```env
VITE_API_BASE_URL=https://api.your-domain.com
VITE_APP_NAME=CBaaS
```

> ⚠️ **Important**: Vite embeds environment variables at **build time**, not runtime. All variables must be prefixed with `VITE_`.

#### Local Frontend Development (without Docker)

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

#### Service Layer Pattern

**Always use the service layer**, never call APIs directly:

```typescript
// ❌ Don't do this
import LoginAPI from 'apis/auth/LoginAPI'
const response = await LoginAPI.login(email, password)

// ✅ Do this
import { AuthService } from 'services/auth/authService'
const response = await AuthService.login(email, password)
```

Services handle:
- Token storage and refresh
- Error formatting
- Business logic
- State updates

---

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
docker compose -f docker-compose.dev.yml exec web pytest

# Run specific test file
docker compose -f docker-compose.dev.yml exec web pytest apps/auth/tests.py

# Run with coverage
docker compose -f docker-compose.dev.yml exec web pytest --cov=apps

# Verbose output
docker compose -f docker-compose.dev.yml exec web pytest -v
```

Configuration in `pytest.ini`:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm run test

# Run tests in CI mode with coverage
npm run test:ci
```

### CI Pipeline

GitHub Actions runs tests on every PR to `main`:

```yaml
# .github/workflows/ci.yml
- Backend: pytest with PostgreSQL + Redis
- Frontend: Vitest with coverage reports
```

---

## 🚢 Deployment

### Architecture Overview

```
GitHub → Actions → ECR → ECS (Fargate) → CloudFront/ALB → Users
   │                                          │
   └──────────────────────────────────────────┘
              (CI/CD on push to release)
```

### Prerequisites

1. **AWS Account** with credentials configured
2. **ECR Repositories** created:
   - `cbaas-frontend`
   - `cbaas-backend`
   - `cbaas-worker`
3. **ECS Cluster** (`cbaas-cluster`)
4. **GitHub Secrets** configured (see below)

### GitHub Secrets Configuration

Add these secrets to your repository (`Settings → Secrets and variables → Actions`):

```
AWS_ACCESS_KEY_ID          # IAM user with ECR/ECS permissions
AWS_SECRET_ACCESS_KEY      # Corresponding secret key
AWS_REGION                 # ap-south-1 (or your region)
ECR_REGISTRY               # 577897067437.dkr.ecr.ap-south-1.amazonaws.com
```

### Automated Deployment (CD Pipeline)

The CI/CD pipeline is triggered on push to the `release` branch:

```bash
# From your development branch
git checkout -b feature/my-feature
# Make changes, commit, test locally

# Merge to release to deploy
git checkout release
git merge feature/my-feature
git push origin release
```

**Deployment Steps** (automated via `.github/workflows/cd.yml`):

1. **Build** Docker images (frontend, backend, worker)
2. **Push** to Amazon ECR
3. **Deploy** to ECS by forcing new service deployments:
   - `frontend-service` (CloudFront distribution)
   - `backend-service` (ALB)
   - `worker-service` (Celery workers)

### Manual Deployment

#### Frontend to CloudFront

```bash
cd infra/aws

# Deploy to CloudFront distribution
./deploy_frontend.sh <bucket-name> <distribution-id>

# Example:
./deploy_frontend.sh cbaas-vite-app E3ACPM7RLVZA5I
```

#### Backend to ECS

```bash
# Build and push manually
cd backend
docker build -f Dockerfile.prod -t cbaas-backend:latest .
docker tag cbaas-backend:latest 577897067437.dkr.ecr.ap-south-1.amazonaws.com/cbaas-backend:latest
docker push 577897067437.dkr.ecr.ap-south-1.amazonaws.com/cbaas-backend:latest

# Update ECS service
aws ecs update-service \
  --cluster cbaas-cluster \
  --service backend-service \
  --force-new-deployment \
  --region ap-south-1
```

### Environment-Specific Settings

Backend loads settings based on `DJANGO_ENV` environment variable:

```python
# backend/config/settings.py
DJANGO_ENV = os.environ.get("DJANGO_ENV", "dev")

if DJANGO_ENV == "prod":
    from .environments.prod import *  # Production settings
elif DJANGO_ENV == "staging":
    from .environments.staging import *  # Staging settings
else:
    from .environments.dev import *  # Development settings
```

**Key differences:**

| Setting | Development | Production |
|---------|------------|------------|
| DEBUG | True | False |
| Database | Local PostgreSQL | AWS RDS |
| Static Files | Whitenoise | S3 + CloudFront |
| CORS | Allow all | Specific origins |
| Logging | Console | CloudWatch |
| Workers | 1 Celery worker | Auto-scaling workers |

### Worker Deployment

Both `web` and `worker` services use the same `Dockerfile.prod`:

```dockerfile
# Dockerfile.prod builds the image
# CMD is overridden in ECS task definition:

# Web service:
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]

# Worker service:
CMD ["celery", "-A", "config.celery.app", "worker", "-l", "info"]
```

---

## 🔐 Environment Variables

### Backend Environment Variables

<details>
<summary>Click to expand complete list</summary>

#### Django Core
```env
DJANGO_ENV=prod                         # Environment: dev, staging, prod
SECRET_KEY=<django-secret-key>          # Django secret key (generate with manage.py)
DEBUG=False                             # Debug mode (False in production)
ALLOWED_HOSTS=api.yourdomain.com        # Comma-separated allowed hosts
```

#### Database
```env
POSTGRES_DB=cbaas                       # Database name
POSTGRES_USER=cbaas                     # Database user
POSTGRES_PASSWORD=<secure-password>     # Database password
POSTGRES_HOST=db                        # Database host
POSTGRES_PORT=5432                      # Database port
```

#### Celery & Redis
```env
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

#### LLM Providers
```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...                   # Optional

# Google Gemini
GEMINI_API_KEY=...

# DeepSeek
DEEPSEEK_API_KEY=...

# Embedding Configuration
EMBEDDING_PROVIDER=openai               # openai, gemini
EMBEDDING_MODEL=text-embedding-3-small  # Model name
EMBEDDING_DIM=1536                      # Embedding dimensions
```

#### AWS (Production)
```env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=cbaas-media
AWS_S3_REGION_NAME=ap-south-1
AWS_S3_CUSTOM_DOMAIN=cdn.yourdomain.com  # Optional CloudFront domain
```

#### Security
```env
CORS_ALLOWED_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://app.yourdomain.com
```

</details>

### Frontend Environment Variables

All frontend env vars must be prefixed with `VITE_`:

```env
# API Configuration
VITE_API_BASE_URL=https://api.yourdomain.com

# App Configuration
VITE_APP_NAME=CBaaS
VITE_APP_VERSION=1.0.0

# Feature Flags
VITE_ENABLE_ANALYTICS=true
```

---

## 📖 API Documentation

### Interactive API Documentation

When running locally, access interactive API docs:

- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### Authentication

CBaaS uses JWT (JSON Web Tokens) for authentication:

```bash
# 1. Login to get tokens
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Response:
{
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}

# 2. Use access token in subsequent requests
curl -X GET http://localhost:8000/api/chatbots/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."

# 3. Refresh access token when expired
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."}'
```

### Key Endpoints

<details>
<summary>Click to expand endpoint reference</summary>

#### Authentication
- `POST /api/auth/signup/` - Register new user
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/auth/logout/` - Logout and blacklist token
- `POST /api/auth/token/refresh/` - Refresh access token
- `GET /api/auth/status/` - Check authentication status

#### Users
- `GET /api/users/me/` - Get current user profile
- `PATCH /api/users/me/` - Update user profile
- `POST /api/users/change-password/` - Change password

#### Organizations
- `GET /api/organizations/` - List user's organizations
- `POST /api/organizations/` - Create new organization
- `GET /api/organizations/{id}/` - Get organization details
- `PATCH /api/organizations/{id}/` - Update organization
- `POST /api/organizations/{id}/invite/` - Invite user to organization

#### Chatbots
- `GET /api/chatbots/` - List chatbots (filtered by organization)
- `POST /api/chatbots/` - Create new chatbot
- `GET /api/chatbots/{id}/` - Get chatbot details
- `PATCH /api/chatbots/{id}/` - Update chatbot configuration
- `DELETE /api/chatbots/{id}/` - Delete chatbot

#### Documents
- `GET /api/documents/` - List documents
- `POST /api/documents/` - Upload document
- `GET /api/documents/{id}/` - Get document details
- `DELETE /api/documents/{id}/` - Delete document
- `GET /api/documents/{id}/chunks/` - Get document chunks

#### Chat
- `GET /api/chat/sessions/` - List chat sessions
- `POST /api/chat/sessions/` - Create chat session
- `GET /api/chat/sessions/{id}/messages/` - Get session messages
- `POST /api/chat/sessions/{id}/messages/` - Send message

#### API Keys
- `GET /api/api-keys/` - List API keys
- `POST /api/api-keys/` - Create API key
- `POST /api/api-keys/test/` - Test API key validity
- `DELETE /api/api-keys/{id}/` - Delete API key

</details>

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes following our coding standards
4. **Test** your changes locally
5. **Commit** with descriptive messages: `git commit -m 'Add amazing feature'`
6. **Push** to your fork: `git push origin feature/amazing-feature`
7. **Open** a Pull Request to `main` branch

### Code Standards

#### Backend (Python)
- Follow **PEP 8** style guide
- Use **type hints** for function signatures
- Write **docstrings** for public methods
- Keep functions **focused** and **single-purpose**
- Add **tests** for new features

```python
def process_document(document: Document, user: User) -> DocumentChunk:
    """
    Process a document and create chunks with embeddings.
    
    Args:
        document: The document to process
        user: The user who owns the document
    
    Returns:
        DocumentChunk: The created chunk with embeddings
    
    Raises:
        ValidationError: If document format is unsupported
    """
    # Implementation
```

#### Frontend (TypeScript)
- Use **TypeScript** strictly (no `any` types)
- Follow **ESLint** configuration
- Use **service layer** for API calls (never direct API imports in components)
- Keep components **small** and **reusable**
- Use **shadcn/ui** components when available

```typescript
// ✅ Good
import { AuthService } from '@/services/auth/authService';

export const LoginPage = () => {
  const handleLogin = async (email: string, password: string) => {
    const result = await AuthService.login(email, password);
    // Handle result
  };
};

// ❌ Bad
import LoginAPI from '@/apis/auth/LoginAPI';

export const LoginPage = () => {
  const handleLogin = async (email: string, password: string) => {
    const result = await LoginAPI.login(email, password);
    // Direct API call
  };
};
```

### Commit Message Convention

Follow conventional commits:

```
feat: Add user profile editing
fix: Resolve token refresh bug
docs: Update deployment instructions
test: Add tests for document processing
refactor: Simplify authentication middleware
chore: Update dependencies
```

---

## 📊 Key Patterns & Best Practices

### Backend

#### 1. Service Layer for Complex Logic

```python
# apps/chatbot/services.py
class ProviderTestService:
    """Service to test LLM provider API keys."""
    
    @staticmethod
    def test_openai(api_key: str) -> dict:
        # Implementation
        pass
```

#### 2. Environment-Based Configuration

Settings are automatically loaded based on `DJANGO_ENV`:
- `dev` → `config/environments/dev.py`
- `staging` → `config/environments/staging.py`
- `prod` → `config/environments/prod.py`

#### 3. Multi-Provider LLM Abstraction

```python
from common.llm.embeddings import get_embedding

# Provider-agnostic embedding generation
embedding = get_embedding(
    text="Hello world",
    provider=settings.EMBEDDING_PROVIDER,
    model=settings.EMBEDDING_MODEL
)
```

#### 4. Async Task Processing

```python
from apps.documents.tasks import process_document_task

# Queue async task
process_document_task.delay(document_id)
```

#### 5. Request Logging Middleware

All requests are logged with unique `request_id` for tracing:
```
[2025-10-07 12:34:56] REQUEST_ID=abc123 | POST /api/chatbots/ | 201 | 0.45s
```

### Frontend

#### 1. Service Layer Pattern

**Never** call APIs directly from components. Always use services:

```typescript
// src/services/auth/authService.ts
export class AuthService {
  static async login(email: string, password: string) {
    const response = await LoginAPI.login(email, password);
    // Handle token storage, state updates
    return response;
  }
}
```

#### 2. Redux State Management

- Use **Redux Toolkit** slices
- Only persist `auth` slice (security)
- Middleware handles token refresh automatically

```typescript
// src/store/slices/authSlice.ts
export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setTokens: (state, action) => {
      state.accessToken = action.payload.access;
      state.refreshToken = action.payload.refresh;
    }
  }
});
```

#### 3. Environment Variables

All env vars must be prefixed with `VITE_` and are embedded at **build time**:

```typescript
const API_URL = import.meta.env.VITE_API_BASE_URL;
```

---

## 🐛 Troubleshooting

### Common Issues

<details>
<summary><strong>Database connection errors</strong></summary>

**Symptom**: `FATAL: password authentication failed`

**Solution**:
```bash
# Recreate database volume
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d
```
</details>

<details>
<summary><strong>Frontend can't connect to backend</strong></summary>

**Symptom**: CORS errors or network errors

**Solution**:
- Check `VITE_API_BASE_URL` in `.env.development`
- Ensure backend is running: `docker compose -f docker-compose.dev.yml ps`
- Check CORS settings in `backend/config/environments/dev.py`
</details>

<details>
<summary><strong>Celery worker not processing tasks</strong></summary>

**Symptom**: Tasks stuck in pending state

**Solution**:
```bash
# Check worker logs
docker compose -f docker-compose.dev.yml logs -f worker

# Restart worker
docker compose -f docker-compose.dev.yml restart worker

# Verify Redis connection
docker compose -f docker-compose.dev.yml exec redis redis-cli ping
```
</details>

<details>
<summary><strong>pgvector extension not found</strong></summary>

**Symptom**: `ERROR: type "vector" does not exist`

**Solution**:
```bash
# Ensure using ankane/pgvector image
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d db

# Run migrations again
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
```
</details>

<details>
<summary><strong>Frontend build fails in production</strong></summary>

**Symptom**: `VITE_API_BASE_URL is not defined`

**Solution**:
- Ensure `.env.production` exists with all required variables
- Remember: Vite embeds vars at **build time**, not runtime
- Rebuild: `npm run build`
</details>

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Django** and **Django REST Framework** teams
- **React** and **Vite** communities
- **shadcn/ui** for beautiful UI components
- **pgvector** for efficient vector similarity search
- **Celery** for robust task queue
- OpenAI, Google, and other LLM providers

---

## 📬 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/ayyadurai-k/CBaaS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ayyadurai-k/CBaaS/discussions)
- **Email**: support@cbaas.example.com

---

## 🗺️ Roadmap

- [ ] WebSocket support for real-time chat
- [ ] Multi-language support (i18n)
- [ ] Advanced analytics dashboard
- [ ] Custom LLM provider integration
- [ ] Mobile app (React Native)
- [ ] Voice chat capabilities
- [ ] Chatbot marketplace
- [ ] A/B testing for chatbot responses

---

<div align="center">

**Built with ❤️ by the CBaaS Team**

[⭐ Star us on GitHub](https://github.com/ayyadurai-k/CBaaS) | [🐛 Report Bug](https://github.com/ayyadurai-k/CBaaS/issues) | [💡 Request Feature](https://github.com/ayyadurai-k/CBaaS/issues)

</div>
